# Local AI Ops

A growing toolbox of plain Python and local AI tools that take repeatable work away from ChatGPT and Claude.

- **Faster:** a script runs in milliseconds; a chat takes minutes.
- **Saves tokens:** files are cleaned and trimmed before an LLM sees them, and many tasks never reach an LLM at all.
- **Same output every time:** rules instead of guesses; local models run at temperature 0 with a fixed seed; every result is cached.

> **The rule:** if you asked an LLM to do the same mechanical thing twice, turn it into a function here. Keep paid LLMs for judgment and writing.

## What's inside

| Module | What it does | Command |
|---|---|---|
| `aiops.core` | SQLite cache (`@cached`), deterministic LLM calls: local Ollama and Claude API, both cached | `aiops llm local "..."` |
| `aiops.text` | clean, remove boilerplate and duplicate lines, trim to a token budget, token estimate, diff, slug, keyword counts | `aiops text compact FILE` |
| `aiops.docs` | PDF, DOCX, HTML, CSV, JSON → plain text | `aiops docs totext FILE --compact` |
| `aiops.youtube` | local Whisper transcription (EN/UR) → SRT, chapters, 1280×720 thumbnails | `aiops yt transcribe video.mp4` |
| `aiops.jobs` | job pipeline: collect, dedupe, visa/language filters, pick CV, fit score, short LLM brief, Notion sync | `aiops jobs run` |
| `aiops.mcp_server` | exposes the tools to Claude Desktop / Claude Code | `aiops mcp` |

## Setup (step by step)

1. Get the code:
   ```bash
   git clone https://github.com/faheemkhaskheli9/Local-AI-Ops.git
   cd Local-AI-Ops
   pip install -e ".[dev]"
   ```
2. Add only the extras you need:
   ```bash
   pip install -e ".[docs]"        # PDF and Word files
   pip install -e ".[youtube]"     # Whisper transcription, thumbnails
   pip install -e ".[jobs]"        # job board search (JobSpy)
   pip install -e ".[embeddings]"  # embedding-based fit score
   pip install -e ".[mcp]"         # use the tools from Claude
   pip install -e ".[all]"         # everything
   ```
3. Optional local model: install [Ollama](https://ollama.com/download), then:
   ```bash
   ollama pull qwen2.5:7b
   ```
   Needs about 8 GB of GPU memory or 16 GB of RAM. Change the model with `AIOPS_LOCAL_MODEL`.
4. Run the tests: `pytest`

## Use the tools from Claude (biggest token saver)

With the MCP server, Claude calls a tool like `file_to_text` instead of reading a 40-page PDF into its context.

- **Claude Code:** `claude mcp add aiops -- aiops mcp`
- **Claude Desktop:** Settings → Developer → Edit Config, then add:
  ```json
  {"mcpServers": {"aiops": {"command": "aiops", "args": ["mcp"]}}}
  ```
  Restart Claude Desktop.

Tools: `file_to_text`, `compact_text`, `count_tokens`, `text_diff`, `job_check`, `srt_to_chapters`, `local_llm`.

## Examples

```bash
# Shrink a page before pasting it into a chat
aiops docs totext job.html --max-tokens 800

# YouTube: transcribe, then chapters from what you say in the video
aiops yt transcribe lesson.mp4 --lang ur
aiops yt chapters lesson.srt --markers "install,load the data,train,evaluate"
aiops yt thumb raw.png thumb

# Structured answer from the local model, same every run
aiops llm local "Classify this ticket: printer is on fire" --schema schema.json
```

### Job pipeline

```bash
cp config.example.yaml config.yaml   # edit keywords, skills, filters
aiops jobs add links.txt             # or: aiops jobs collect (JobSpy)
aiops jobs run                       # filter, pick CV, score
aiops jobs list                      # shortlist, best first
aiops jobs list --status filtered_out
aiops jobs brief                     # short prompts for Claude in briefs/
aiops jobs sync                      # push shortlist to Notion (NOTION_TOKEN)
```

Optional data files: `data/target_companies.csv` (`company,status` — `Skip`/`Applied` are filtered out) and `data/ind_sponsors.csv` (`name`) from the IND [public register of recognised sponsors](https://ind.nl/en/public-register-recognised-sponsors). LinkedIn forbids scraping, so keep volumes low or feed links in with `aiops jobs add`.

## Use it from Python

```python
from aiops.core import cached
from aiops.core import llm
from aiops.text.ops import compact
from aiops.docs.extract import to_text

text = compact(to_text("report.pdf"), max_tokens=1500)
facts = llm.local(f"Extract the dates:\n{text}", schema={"type": "object", ...})

@cached("my-step")          # result stored in ~/.cache/aiops/cache.db
def slow_step(x): ...
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system design: how ChatGPT and Claude connect, security, caching and roadmap.

## Add a new tool

See [CLAUDE.md](CLAUDE.md). In short: one module per area, a pure function, a test, a CLI command, and an MCP tool if Claude should call it.

## Privacy

`config.yaml`, `cvs/`, `data/`, `briefs/`, `*.db` and `.env` are git-ignored. Never commit CVs, keys or personal data.

## License

MIT

## Shared tools for OpenAI, Anthropic and MCP

The seven existing MCP tools now come from a single registry (`aiops.registry` and
`aiops.tool_catalog`). The original Python implementations and provider
integrations are **reused**, not recreated.

Export API function-call schemas without running any models or services:

```bash
python -m aiops.export openai > openai-tools.json
python -m aiops.export openai-chat > openai-chat-tools.json
python -m aiops.export anthropic > anthropic-tools.json
```

Call the same existing functions from a trusted local executor:

```python
from aiops.registry import dispatch
result = dispatch("count_tokens", {"text": "A compact context"})
```

The exporter produces schemas only; **it does not automatically register tools
in ChatGPT or Claude**. Local MCP remains `aiops mcp`. All catalog tools
are blocked from remote dispatch by default. See
[plugin and tool reuse policy](docs/REUSE_POLICY.md) before adding new ones.
