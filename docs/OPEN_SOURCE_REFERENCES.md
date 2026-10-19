# Open-Source References — Local-AI-Ops

Candidate repositories to review and possibly integrate. Stack: Python CLI + MCP.

Status values: `To review` → `Evaluating` → `Adopted` / `Rejected`. Licenses are as last known; verify before use. AGPL/GPL/source-available licenses can restrict commercial or SaaS use.

## Local inference

### [ollama/ollama](https://github.com/ollama/ollama)
- **What:** Run open LLMs locally with a simple API.
- **Possible use:** Default local backend for `aiops llm local` (already used).
- **License:** MIT
- **Status:** To review

### [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp)
- **What:** CPU/edge LLM inference with quantized GGUF models.
- **Possible use:** CPU-only / low-RAM machines; GGUF quantized models.
- **License:** MIT
- **Status:** To review

### [vllm-project/vllm](https://github.com/vllm-project/vllm)
- **What:** High-throughput LLM inference and serving.
- **Possible use:** High-throughput batch jobs when a GPU is available.
- **License:** Apache-2.0
- **Status:** To review

### [BerriAI/litellm](https://github.com/BerriAI/litellm)
- **What:** One OpenAI-style API/proxy for 100+ LLM providers, with budgets and fallbacks.
- **Possible use:** One interface for Ollama + cloud models; routing, fallbacks, cost caps.
- **License:** MIT (enterprise separate)
- **Status:** To review

## Document & media

### [docling-project/docling](https://github.com/docling-project/docling)
- **What:** Document parsing: PDF, DOCX, tables and layout to structured text.
- **Possible use:** Higher-quality PDF/DOCX/table extraction for `docs totext`.
- **License:** MIT
- **Status:** To review

### [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- **What:** Multilingual OCR toolkit (incl. Urdu/Arabic scripts).
- **Possible use:** OCR for scanned PDFs and images.
- **License:** Apache-2.0
- **Status:** To review

### [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- **What:** Fast Whisper speech-to-text (supports Urdu).
- **Possible use:** Transcription for YouTube SRT/chapter workflows (already referenced).
- **License:** MIT
- **Status:** To review

## Reliability & evaluation

### [567-labs/instructor](https://github.com/567-labs/instructor)
- **What:** Structured, validated LLM outputs with Pydantic.
- **Possible use:** Schema-validated outputs from local models.
- **License:** MIT
- **Status:** To review

### [langfuse/langfuse](https://github.com/langfuse/langfuse)
- **What:** LLM observability: tracing, prompt management, evals.
- **Possible use:** Trace calls, compare local vs cloud quality and token savings.
- **License:** MIT (ee/ separate)
- **Status:** To review

### [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo)
- **What:** Prompt/LLM testing, comparison and red-teaming.
- **Possible use:** Regression tests for prompts used by aiops tools.
- **License:** MIT
- **Status:** To review

### [explodinggradients/ragas](https://github.com/explodinggradients/ragas)
- **What:** Evaluation metrics for RAG pipelines.
- **Possible use:** Evaluate any RAG/knowledge-base features.
- **License:** Apache-2.0
- **Status:** To review

### [qdrant/qdrant](https://github.com/qdrant/qdrant)
- **What:** Vector database for semantic search and RAG.
- **Possible use:** Local vector store for notes/knowledge base search.
- **License:** Apache-2.0
- **Status:** To review

## Automation & UI

### [n8n-io/n8n](https://github.com/n8n-io/n8n)
- **What:** Workflow automation with 400+ integrations.
- **Possible use:** Schedule aiops jobs and connect to other apps without code.
- **License:** Sustainable Use License
- **Status:** To review

### [open-webui/open-webui](https://github.com/open-webui/open-webui)
- **What:** Chat UI for local and API models.
- **Possible use:** Chat UI over the same local models.
- **License:** BSD-3 + branding clause
- **Status:** To review
