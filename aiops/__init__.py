"""aiops: deterministic tools that save LLM tokens.

Rule of thumb: if you asked an LLM to do the same mechanical thing twice,
it belongs here as a function. LLMs are for judgment and writing only.

Modules
- aiops.core     cache, deterministic LLM calls (Ollama / Claude), helpers
- aiops.text     clean, trim to budget, token estimate, diff, slugs
- aiops.docs     extract text from PDF, DOCX, HTML, Markdown
- aiops.youtube  chapters, SRT, thumbnails, local transcription
- aiops.jobs     job pipeline: collect, filter, pick CV, score, brief, Notion
"""

__version__ = "0.2.0"
