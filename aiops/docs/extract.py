"""Turn files into plain text without an LLM.

Supported: .txt .md .html/.htm (stdlib), .pdf (pypdf), .docx (python-docx),
.csv/.json (stdlib). Install extras with: pip install -e ".[docs]"
"""
from __future__ import annotations

import csv
import io
import json
import re
from html.parser import HTMLParser
from pathlib import Path

# Script and style hold raw text; the parser never sees tags inside them.
RAW_TAGS = {"script", "style"}
# Never skip wrappers that may hold the main content (form, header, main).
SKIP_TAGS = RAW_TAGS | {"noscript", "nav", "footer", "svg", "template", "select", "datalist"}
VOID_TAGS = {"area", "base", "basefont", "br", "col", "embed", "frame", "hr", "img",
             "input", "keygen", "link", "meta", "param", "source", "track", "wbr"}
BLOCK_TAGS = {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6",
              "section", "article", "ul", "ol", "table", "pre", "blockquote",
              "header", "footer", "nav", "main", "form", "aside"}
# Start tags that end an open <p>, unless a scope element sits between them.
P_CLOSERS = {"address", "article", "aside", "blockquote", "details", "div", "dl", "dd",
             "dt", "fieldset", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5",
             "h6", "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section",
             "table", "ul"}
P_SCOPE = {"button", "caption", "html", "object", "table", "td", "th", "template"}
# Start tag -> (open elements it implicitly ends, scope elements that stop the search).
AUTO_CLOSE = {
    "li": ({"li"}, {"ul", "ol", "menu"}),
    "dt": ({"dt", "dd"}, {"dl"}),
    "dd": ({"dt", "dd"}, {"dl"}),
    "option": ({"option"}, {"select", "datalist", "optgroup"}),
    "optgroup": ({"option", "optgroup"}, {"select", "datalist"}),
    "tr": ({"tr"}, {"table", "thead", "tbody", "tfoot"}),
    "td": ({"td", "th"}, {"tr", "table"}),
    "th": ({"td", "th"}, {"tr", "table"}),
}
# Often left unclosed, so their end tags never end a skipped element opened inside them.
LOOSE_END_TAGS = {"p", "li", "dt", "dd", "option", "tr", "td", "th"}
# No bound for an unclosed skipped element was found: keep its text rather than lose the page.
KEEP_ON_CLOSE = {"body", "html"}


class _HTMLText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.open: list[str] = []  # open elements, to recover from unclosed tags
        self.depths: dict[str, list[int]] = {}  # tag -> its depths in self.open
        self.skipped: list[tuple[int, int]] = []  # (depth, index in parts) per skipped element
        self.raw = 0  # open script/style elements

    def _nearest(self, tags) -> int:
        return max((self.depths[t][-1] for t in tags if self.depths.get(t)), default=-1)

    def _close(self, depth: int, keep: bool = False) -> None:
        """Close the element at `depth` and every element inside it."""
        for tag in reversed(self.open[depth:]):
            self.depths[tag].pop()
            if tag in RAW_TAGS:
                self.raw -= 1
        del self.open[depth:]
        while self.skipped and self.skipped[-1][0] >= depth:
            _, start = self.skipped.pop()
            if not keep:
                del self.parts[start:]

    def _autoclose(self, tags, scope) -> None:
        depth = self._nearest(tags)
        inner_skip = self.skipped[-1][0] if self.skipped else -1
        if depth > self._nearest(scope) and depth > inner_skip:
            tag = self.open[depth]
            self._close(depth)
            if tag in BLOCK_TAGS:
                self.parts.append("\n")

    def handle_starttag(self, tag, attrs):
        if tag in P_CLOSERS:
            self._autoclose({"p"}, P_SCOPE)
        if tag in AUTO_CLOSE:
            self._autoclose(*AUTO_CLOSE[tag])
        if tag == "main":  # <main> is never inside nav/footer: end an unclosed one
            menus = [self.depths[t][0] for t in ("nav", "footer") if self.depths.get(t)]
            if menus:
                self._close(min(menus))
        if tag in VOID_TAGS:
            if tag == "br":
                self.parts.append("\n")
            return
        if tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag in SKIP_TAGS:
            self.skipped.append((len(self.open), len(self.parts)))
        self.depths.setdefault(tag, []).append(len(self.open))
        self.open.append(tag)
        if tag in RAW_TAGS:
            self.raw += 1
        if tag == "li":
            self.parts.append("- ")
        if tag in {"h1", "h2", "h3"}:
            self.parts.append("#" * int(tag[1]) + " ")

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        depth = self.depths[tag][-1] if self.depths.get(tag) else -1
        if tag in LOOSE_END_TAGS and self.skipped and depth < self.skipped[-1][0]:
            depth = -1  # stray: the match is outside the skipped element
        if depth >= 0:
            self._close(depth, keep=tag in KEEP_ON_CLOSE)
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.raw:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    p = _HTMLText()
    p.feed(html)
    p.close()  # flush text after the last tag
    text = "".join(p.parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def pdf_to_text(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()


def docx_to_text(path: Path) -> str:
    import docx

    d = docx.Document(str(path))
    lines = []
    for para in d.paragraphs:
        style = (para.style.name or "").lower() if para.style is not None else ""
        txt = para.text.strip()
        if not txt:
            continue
        if style.startswith("heading"):
            level = re.sub(r"\D", "", style) or "1"
            lines.append("#" * int(level) + " " + txt)
        elif "list" in style:
            lines.append("- " + txt)
        else:
            lines.append(txt)
    for table in d.tables:
        for row in table.rows:
            lines.append(" | ".join(c.text.strip() for c in row.cells))
    return "\n\n".join(lines)


def csv_to_text(text: str, max_rows: int = 50) -> str:
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return ""
    head, body = rows[0], rows[1:max_rows + 1]
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(r) + " |" for r in body]
    if len(rows) - 1 > max_rows:
        out.append(f"... {len(rows) - 1 - max_rows} more rows")
    return "\n".join(out)


def to_text(path: str | Path) -> str:
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".pdf":
        return pdf_to_text(path)
    if ext == ".docx":
        return docx_to_text(path)
    raw = path.read_text(encoding="utf-8", errors="replace")
    if ext in {".html", ".htm"}:
        return html_to_text(raw)
    if ext == ".csv":
        return csv_to_text(raw)
    if ext == ".json":
        return json.dumps(json.loads(raw), indent=1, ensure_ascii=False)
    return raw
