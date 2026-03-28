# Automated Book Generation System

A modular, production-grade system that accepts a book title, generates an outline, writes chapters with context chaining, and compiles a final draft — with human-in-the-loop review at every stage.

---

## Tech Stack

| Component         | Tool                        |
|-------------------|-----------------------------|
| Automation Engine | n8n                         |
| Backend API       | FastAPI (Python)            |
| Database          | Supabase (PostgreSQL)       |
| AI Model          | OpenAI GPT-4o               |
| Input Source      | Excel (.xlsx)               |
| Notifications     | SMTP Email + MS Teams       |
| Output Files      | .docx, .pdf, Supabase Storage |

---

## Architecture
```
Excel Input → FastAPI /parse-input → Supabase (books table)
     ↓
n8n Outline Workflow → FastAPI /outline/generate → OpenAI → Supabase (outlines table)
     ↓
n8n Chapter Workflow → FastAPI /chapters/generate → OpenAI (with summary chaining) → Supabase (chapters table)
     ↓
n8n Compilation Workflow → FastAPI /compile → .docx + .pdf → Supabase Storage
     ↓
Email + MS Teams notifications at every stage
```

---

## Quick Start

### 1. Clone and configure
```bash
git clone <repo-url>
cd book_generator
cp .env.example .env
# fill in your actual keys in .env
```

### 2. Run with Docker
```bash
docker-compose up --build
```

- FastAPI: `http://localhost:8000`
- FastAPI Docs: `http://localhost:8000/docs`
- n8n: `http://localhost:5678` (admin / admin123)

### 3. Run without Docker
```bash
pip install -r requirements.txt
uvicorn fastapi_service.main:app --reload
```

---

## Workflow

### Stage 1 — Input & Outline

1. Fill in `input/books_input.xlsx` with title and notes
2. Call `POST /api/parse-input` to load book into DB
3. n8n detects pending book and calls `POST /api/outline/generate`
4. Editor reviews outline in Supabase, adds notes if needed
5. Call `POST /api/outline/regenerate` to revise with editor notes

### Stage 2 — Chapter Generation

1. n8n chapter workflow triggered after outline approval
2. Each chapter generated with full context of previous chapter summaries
3. Editor can add notes per chapter and trigger regeneration
4. Each chapter stores both full content and a short summary

### Stage 3 — Final Compilation

1. All chapters marked `approved` in Supabase
2. Set `final_review_notes_status = no_notes_needed`
3. n8n compilation workflow calls `POST /api/compile`
4. `.docx` and `.pdf` exported and uploaded to Supabase Storage
5. Editor notified via email and Teams with download links

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/parse-input` | Parse Excel and insert books |
| GET | `/api/books/pending` | Get all pending books |
| GET | `/api/books/{book_id}` | Get single book record |
| PATCH | `/api/books/status` | Update a book status field |
| POST | `/api/outline/generate` | Generate outline for a book |
| POST | `/api/outline/regenerate` | Regenerate outline with new notes |
| POST | `/api/chapters/generate` | Generate all chapters |
| POST | `/api/chapters/regenerate` | Regenerate a single chapter |
| POST | `/api/compile` | Compile final .docx and .pdf |
| GET | `/health` | Health check |

---

## Database Schema

| Table | Purpose |
|-------|---------|
| `books` | Master record per book with all status fields |
| `outlines` | Versioned outline history per book |
| `chapters` | Individual chapter content and summaries |
| `notifications_log` | Audit trail of all notifications sent |

---

## n8n Workflows

Located in `n8n_workflows/`. Import them directly into n8n:

1. `outline_workflow.json` — polls for pending books, generates outline, notifies editor
2. `chapter_workflow.json` — generates all chapters with review gating
3. `compilation_workflow.json` — final gate check, compiles book, sends download link

---

## Design Decisions

- **FastAPI over pure n8n scripting** — complex logic like summary chaining, prompt building, and document compilation belongs in clean Python code, not drag-and-drop nodes
- **GPT-4o** — best balance of writing quality and speed for long-form content
- **Versioned outlines** — every regeneration creates a new version row, nothing is ever overwritten, full history preserved
- **Summary chaining** — each chapter receives summaries of all previous chapters as context, ensuring narrative consistency across the full book
- **Supabase Storage** — output files stored in the cloud with public URLs sent directly in notifications

---

## Project Structure
```
book_generator/
├── fastapi_service/
│   ├── api/routes/          # FastAPI route handlers
│   ├── core/                # Config and DB connection
│   ├── db/                  # Supabase client helpers
│   ├── services/            # Business logic
│   └── utils/               # Prompt builder, docx, pdf
├── n8n_workflows/           # Exported n8n JSON files
├── db/                      # SQL migration files
├── input/                   # Excel input file
├── output/                  # Generated .docx and .pdf
├── tests/                   # Phase test scripts
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```