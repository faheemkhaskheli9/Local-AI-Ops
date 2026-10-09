"""YouTube helpers: chapters, SRT, thumbnails, local transcription."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Segment:
    start: float  # seconds
    end: float
    text: str


def fmt_ts(seconds: float) -> str:
    """YouTube chapter timestamp: 0:00, 4:05, 1:02:03."""
    s = int(seconds)
    h, m, s = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def fmt_srt_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_srt(segments: list[Segment]) -> str:
    return "\n".join(
        f"{i}\n{fmt_srt_ts(seg.start)} --> {fmt_srt_ts(seg.end)}\n{seg.text.strip()}\n"
        for i, seg in enumerate(segments, 1)
    )


def parse_srt(text: str) -> list[Segment]:
    def secs(ts: str) -> float:
        h, m, rest = ts.replace(",", ".").split(":")
        return int(h) * 3600 + int(m) * 60 + float(rest)

    segs = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().splitlines()
        if len(lines) >= 2 and "-->" in lines[1]:
            a, b = (x.strip() for x in lines[1].split("-->"))
            segs.append(Segment(secs(a), secs(b), " ".join(lines[2:])))
    return segs


def chapters_from_markers(segments: list[Segment], markers: dict[str, str] | list[str],
                          min_gap: float = 10.0) -> list[tuple[float, str]]:
    """Chapters where the speaker says a marker phrase.

    `markers`: list of phrases (title = phrase) or {phrase: chapter title}.
    Example: {"first let's install": "Setup", "now we train": "Training"}.
    YouTube needs the first chapter at 0:00 and each at least 10 s long.
    """
    m = {p: p.title() for p in markers} if isinstance(markers, list) else markers
    out: list[tuple[float, str]] = [(0.0, "Intro")]
    for seg in segments:
        low = seg.text.lower()
        for phrase, title in m.items():
            if phrase.lower() in low and seg.start - out[-1][0] >= min_gap \
                    and title not in {t for _, t in out}:
                out.append((seg.start, title))
    return out


def chapters_by_gap(segments: list[Segment], pause: float = 2.5,
                    min_len: float = 60.0, words: int = 6) -> list[tuple[float, str]]:
    """Fallback: start a chapter after a long pause, titled by its first words."""
    out: list[tuple[float, str]] = [(0.0, "Intro")]
    for prev, seg in zip(segments, segments[1:]):
        if seg.start - prev.end >= pause and seg.start - out[-1][0] >= min_len:
            title = " ".join(seg.text.split()[:words]).rstrip(",.") or "Part"
            out.append((seg.start, title[0].upper() + title[1:]))
    return out


def chapters_text(chapters: list[tuple[float, str]]) -> str:
    return "\n".join(f"{fmt_ts(t)} {title}" for t, title in chapters)


def thumbnail(src: str | Path, dst: str | Path, size=(1280, 720),
              max_bytes: int = 2_000_000) -> Path:
    """Center-crop and resize to 16:9, save as JPEG under YouTube's 2 MB limit."""
    from PIL import Image, ImageOps

    img = ImageOps.fit(Image.open(src).convert("RGB"), size, Image.LANCZOS)
    dst = Path(dst).with_suffix(".jpg")
    for q in (95, 90, 85, 80, 75, 70, 60):
        img.save(dst, "JPEG", quality=q, optimize=True)
        if dst.stat().st_size <= max_bytes:
            break
    return dst


def transcribe(audio: str | Path, model: str = "small", language: str | None = None,
               device: str = "auto") -> list[Segment]:
    """Local speech-to-text with faster-whisper (greedy decoding = repeatable).

    language: "en", "ur", or None to auto-detect.
    """
    from faster_whisper import WhisperModel

    m = WhisperModel(model, device=device, compute_type="auto")
    segs, _ = m.transcribe(str(audio), language=language, beam_size=1,
                           temperature=0.0, vad_filter=True)
    return [Segment(s.start, s.end, s.text.strip()) for s in segs]
