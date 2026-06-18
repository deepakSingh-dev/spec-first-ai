# SpecAI — Constraints-First AI Coding Workflow

> **Generate production-ready code that provably satisfies every requirement.**
> SpecAI extracts structured constraints from a plain-English spec, auto-generates
> and runs a test suite against those constraints, scores quality across six
> engineering dimensions, and retries until the code passes — all driven by a
> local LLM through a LangGraph state machine.

---

## Table of Contents

- [Why SpecAI?](#why-specai)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)
- [Docker Deployment](#docker-deployment)
- [Configuration](#configuration)
- [Roadmap](#roadmap)
- [License](#license)

---

## Why SpecAI?

Most AI coding assistants generate code based on vibes. SpecAI flips the model:

1. **Spec first** — you write a natural-language specification with title, description, and requirements.
2. **Constraints extracted** — an LLM acting as a senior architect extracts every functional, performance, security, type-safety, and edge-case constraint into a structured, severity-ranked list.
3. **Tests generated** — a second LLM pass produces a complete pytest suite covering each constraint.
4. **Tests run in isolation** — each test case runs in a sandboxed subprocess so bad code can never corrupt the host process.
5. **Quality scored** — a principal-engineer persona scores the implementation across six dimensions and decides compliance.
6. **Auto-retry** — if tests fail or quality is below threshold, the pipeline regenerates code and retries up to a configurable limit.

The result: code you can trust, with a machine-verified paper trail from spec to passing tests.

---

## Architecture

```
                       ┌─────────────────────────────────────────────┐
                       │              LangGraph State Machine         │
                       │                                              │
POST /specs            │   ┌──────────────┐                          │
──────────────────────►│   │  parse_spec  │  extract_constraints()   │
       SpecRequest     │   │  (LLM call)  │◄─────────────────────────┤
                       │   └──────┬───────┘                          │
                       │          │ list[Constraint]                  │
                       │   ┌──────▼───────┐                          │
                       │   │  gen_tests   │  generate_code()          │
                       │   │  (LLM call)  │  4096-token budget        │
                       │   └──────┬───────┘                          │
                       │          │ (code, list[TestCase])            │
                       │   ┌──────▼───────┐                          │
                       │   │  run_tests   │  subprocess per test      │
                       │   │  (no LLM)    │  30s timeout, isolated    │
                       │   └──────┬───────┘                          │
                       │          │ ┌─── any failed? retry_count < N ─┤
                       │          │ │              ▲                  │
                       │          │ └──────────────┘  node_retry      │
                       │   ┌──────▼───────┐                          │
                       │   │ score_quality│  score_quality()          │
                       │   │  (LLM call)  │  6-dim QualityReport      │
                       │   └──────┬───────┘                          │
                       │          │ LangGraphState → SpecResult       │
                       └──────────┼──────────────────────────────────┘
                                  │
                       GET /specs/{id}
                       ◄──────────┘
```

### Pipeline Stages

| Stage | File | What it does |
|---|---|---|
| Constraint extraction | `backend/pipeline/constraint_extractor.py` | Parses spec → structured `Constraint` objects with severity |
| Code + test generation | `backend/pipeline/code_generator.py` | Produces full implementation + pytest suite in one LLM call |
| Isolated test runner | `backend/pipeline/test_runner.py` | Runs each test in a temp dir subprocess, captures pass/fail |
| Quality scorer | `backend/quality/scorer.py` | Six-dimension LLM review: correctness, completeness, type safety, security, maintainability, test coverage |
| State machine | `backend/langgraph/graph.py` | LangGraph `StateGraph` wiring all stages with conditional retry routing |
| REST API | `backend/api/routes.py` | Async FastAPI — submit spec, poll status, retrieve report |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11+ |
| **API framework** | FastAPI + Uvicorn (async, ASGI) |
| **AI orchestration** | LangGraph (StateGraph, conditional edges, retry routing) |
| **Data validation** | Pydantic v2 (strict models, field constraints) |
| **LLM backend** | Qwen2.5-Coder via Ollama — fully local, no cloud API calls |
| **LLM protocol** | OpenAI-compatible `/v1/chat/completions` (drop-in for any local model) |
| **Testing** | pytest + pytest-asyncio, subprocess isolation, real-file temp dirs |
| **Containerization** | Docker (multi-stage, non-root), docker-compose |
| **Config** | python-dotenv, environment variables |

**Keywords:** `FastAPI` `LangGraph` `LangChain` `Pydantic v2` `asyncio` `Python 3.11` `local LLM` `Ollama` `Qwen` `OpenAI-compatible API` `pytest` `pytest-asyncio` `Docker` `docker-compose` `REST API` `code generation` `AI agent` `multi-agent` `state machine` `constraint-driven development` `spec-first` `automated testing` `quality scoring` `subprocess isolation` `ASGI` `Uvicorn`

---

## Project Structure

```
specai/
├── backend/
│   ├── models.py                  # Pydantic v2 data models (single source of truth)
│   ├── llm_client.py              # All LLM calls go through here — swap model in one place
│   ├── api/
│   │   └── routes.py              # FastAPI router: POST /specs, GET /specs/{id}, etc.
│   ├── pipeline/
│   │   ├── constraint_extractor.py
│   │   ├── code_generator.py
│   │   └── test_runner.py
│   ├── quality/
│   │   └── scorer.py
│   └── langgraph/
│       └── graph.py               # StateGraph wiring + run_spec_pipeline()
├── tests/
│   ├── test_constraint_extractor.py
│   ├── test_code_generator.py
│   ├── test_test_runner.py
│   ├── test_scorer.py
│   ├── test_graph.py
│   └── test_routes.py
├── docker/
│   └── Dockerfile                 # Multi-stage, non-root, python:3.11-slim
├── docker-compose.yml
├── main.py                        # Uvicorn entrypoint
├── requirements.txt
├── pyproject.toml                 # pytest asyncio_mode = auto
├── .env.example
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) running locally with a Qwen model pulled:
  ```bash
  ollama pull qwen2.5-coder:32b
  ```

### Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/YOUR_USERNAME/spec-first-ai.git
cd spec-first-ai

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env to point LLM_BASE_URL at your Ollama instance if not localhost

# 5. Start the API server
uvicorn main:app --reload
```

The API is now live at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## API Reference

### Submit a spec

```bash
curl -X POST http://localhost:8000/specs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "URL shortener service",
    "description": "A REST API that creates short URLs and redirects to originals",
    "natural_language_spec": "The service must accept a long URL via POST /shorten and return a 6-character alphanumeric code. GET /{code} must redirect to the original URL. Codes must be unique. Invalid or expired codes return 404. The implementation must be type-annotated and handle concurrent requests safely.",
    "language": "python"
  }'
```

Response `202 Accepted`:
```json
{
  "spec_id": "d3f1a2b4-...",
  "status": "validating",
  "created_at": "2026-06-18T10:00:00Z"
}
```

### Poll for results

```bash
curl http://localhost:8000/specs/d3f1a2b4-...
```

### Get quality report

```bash
curl http://localhost:8000/specs/d3f1a2b4-.../quality
```

### All endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/specs` | Submit a new spec (async, returns 202) |
| `GET` | `/specs` | List recent results (newest first, max 100) |
| `GET` | `/specs/{id}` | Get full result including code and tests |
| `GET` | `/specs/{id}/quality` | Get quality report (409 if not complete) |
| `DELETE` | `/specs/{id}` | Remove a result |

---

## Running Tests

```bash
# All tests
pytest -v

# Individual suites
pytest tests/test_constraint_extractor.py -v
pytest tests/test_code_generator.py -v
pytest tests/test_test_runner.py -v          # spawns real subprocesses
pytest tests/test_scorer.py -v
pytest tests/test_graph.py -v
pytest tests/test_routes.py -v

# Single test
pytest tests/test_graph.py::test_retry_path -v
```

All tests mock the LLM layer — no local model required to run the test suite.
The test runner suite (`test_test_runner.py`) spawns real Python subprocesses; it is intentionally slower than the others.

---

## Docker Deployment

```bash
# Build and start
docker compose up --build

# Verify
curl http://localhost:8000/health
# {"status": "ok", "store_size": 0}
```

The Docker image uses a non-root user and a multi-stage build to keep the final image small. Mount your `.env` file to configure the LLM endpoint:

```yaml
# docker-compose.yml excerpt
env_file:
  - .env
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:11434/v1` | Base URL of your OpenAI-compatible LLM endpoint |
| `LLM_MODEL_NAME` | `qwen2.5-coder:32b` | Model tag passed to the completions API |

Because all LLM calls are funnelled through `backend/llm_client.py::call_llm`, swapping to any OpenAI-compatible backend (OpenAI, Anthropic via proxy, vLLM, LM Studio, llama.cpp server) requires changing only these two env vars.

---

## Roadmap

- [ ] Streaming status updates via Server-Sent Events
- [ ] Persistent storage (PostgreSQL + SQLAlchemy async)
- [ ] Web UI — spec submission form and live pipeline progress view
- [ ] Support for TypeScript / Go generation targets
- [ ] Constraint severity weighting in quality scoring
- [ ] GitHub Action: run SpecAI on every PR to validate implementation against spec

---

## License

MIT — see [LICENSE](LICENSE).
