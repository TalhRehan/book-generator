# Automated Book Generation System

A modular, production-grade system that accepts a book title, generates an outline, writes chapters with context chaining, and compiles a final draft — with human-in-the-loop review at every stage.

---

## Methodology — Agile Iterative Development

This project was built following **Agile methodology** with an iterative, milestones-by-milestones approach.

Rather than building everything at once, the system was developed in small, meaningful increments — each milestones fully working and tested before moving to the next. This mirrors how real production systems are built in professional engineering teams.

**Milestones breakdown:**

| Milestones | What Was Built |
|-------|---------------|
| 1 | Foundation — project structure, environment config, Supabase schema, DB connection |
| 2 | Input parsing — Excel reader, validation, book insertion into Supabase |
| 3 | AI layer — OpenAI wrapper with retry logic, prompt engineering module |
| 4 | Outline generation — GPT-4o outline creation, versioning, regeneration with editor notes |
| 5 | Chapter generation — per-chapter writing, summary-based context chaining, regeneration |
| 6 | Notification system — SMTP email and MS Teams webhook on every pipeline event |
| 7 | Final compilation — .docx and .pdf generation, Supabase Storage upload |
| 8 | Orchestration — Python polling orchestrator tying all stages together |
| 9 | Editor simulation — automated quality-based review and approval layer |
| 10 | Polish — cleanup, full pipeline test, submission prep |

**Key Agile principles applied:**

- **MVP first** — core pipeline (input → outline → chapters → compile) built and working before any extras
- **Iterative improvement** — outline versioning, retry logic, and editor simulation added in later iterations
- **Modular design** — each service is independently testable and replaceable
- **Continuous testing** — every milestones had its own test script before moving forward
- **Working software over documentation** — system runs end to end with zero manual intervention

---

## Tech Stack

| Component | Tool |
|-----------|------|
| Automation Engine | Python Orchestrator |
| Backend API | FastAPI (Python) |
| Database | Supabase (PostgreSQL) |
| AI Model | OpenAI GPT-4o |
| Input Source | Excel (.xlsx) |
| Notifications | SMTP Email + MS Teams Webhook |
| Output Files | .docx, .pdf, Supabase Storage |

---

## Architecture
```
Excel Input
    ↓
Orchestrator — polls every 60 seconds
    ↓
Stage 1: Outline Generation
  → GPT-4o generates outline from title + editor notes
  → Stored in Supabase with full version history
  → Editor reviews → approves or requests revision
    ↓
Stage 2: Chapter Generation
  → Each chapter generated individually
  → Previous chapter summaries passed as context (context chaining)
  → Editor reviews each chapter → approves or requests revision
    ↓
Stage 3: Final Compilation
  → All approved chapters compiled into .docx and .pdf
  → Files uploaded to Supabase Storage
  → Editor notified with download links
    ↓
Notifications — Email + MS Teams at every stage
```

---

## Key Design Decisions

**1. Prompt Engineering Layer**
All GPT prompts live in `utils/prompt_builder.py` as named functions — not inline strings scattered across the codebase. Changing tone, word count, or structure requires editing one file.

**2. Chapter Context Chaining**
Each chapter stores a 150-word summary immediately after generation. Before writing Chapter N, all summaries from Chapters 1 to N-1 are fetched from Supabase and passed as context to GPT-4o. This ensures narrative consistency across the full book without hitting token limits.

**3. Versioned Outline History**
Every outline regeneration creates a new row in the `outlines` table with an incremented version number. Nothing is ever overwritten. Full revision history is preserved and recoverable.

**4. Retry Logic**
Every OpenAI API call is wrapped in exponential backoff retry logic — 3 attempts with increasing delays. A single network hiccup does not crash the pipeline.

**5. FastAPI as Integration Gateway**
The orchestrator handles internal automation directly via Python function calls. FastAPI exposes the same functionality as HTTP endpoints — making the system ready for any external integration: a frontend dashboard, a third-party tool, or a future n8n workflow.

**6. Human-in-the-Loop Gating**
The pipeline never proceeds without explicit approval at each stage. Status fields (`status_outline_notes`, `chapter_notes_status`, `final_review_notes_status`) act as gates. The orchestrator checks these every cycle — pausing, resuming, or notifying based on their values.

---

## Running the System

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# fill in your keys
```

### 3. Set up Supabase

Run `db/migrations/001_initial_schema.sql` in your Supabase SQL editor.

Create a storage bucket named `book-outputs` and set it to public.

### 4. Add your book to Excel

Fill in `input/books_input.xlsx` with at minimum:
- `title`
- `notes_on_outline_before`

### 5. Start the system

**Terminal 1 — API Server:**
```bash
uvicorn fastapi_service.main:app --reload
```

**Terminal 2 — Orchestrator:**
```bash
python -m fastapi_service.orchestrator
```

**Terminal 3 — Editor Simulator (optional for demo):**
```bash
python -m fastapi_service.editor_simulator
```

The orchestrator polls every 60 seconds and automatically moves the book through every stage.

---

## Human-in-the-Loop Flow

In production, the editor interacts with the system by updating status fields — either via the API or directly in Supabase:

| Action | Field to Update | Value |
|--------|----------------|-------|
| Approve outline | `status_outline_notes` | `no_notes_needed` |
| Request outline revision | `status_outline_notes` + `notes_on_outline_after` | `yes` + revision notes |
| Approve a chapter | `chapters.status` | `approved` |
| Request chapter revision | `chapter_notes_status` + `chapter_notes` | `yes` + revision notes |
| Approve final compilation | `final_review_notes_status` | `no_notes_needed` |

The orchestrator detects these changes automatically on the next poll cycle — no restart required.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/parse-input` | Parse Excel and insert books into Supabase |
| GET | `/api/books/pending` | Get all books awaiting processing |
| GET | `/api/books/{book_id}` | Get a single book record |
| POST | `/api/outline/generate` | Generate outline for a book |
| POST | `/api/outline/regenerate` | Regenerate outline with editor notes |
| POST | `/api/chapters/generate` | Generate all chapters for a book |
| POST | `/api/chapters/regenerate` | Regenerate a single chapter |
| POST | `/api/compile` | Compile final .docx and .pdf |
| GET | `/health` | Health check |

Full interactive documentation available at `http://localhost:8000/docs`

---

## Database Schema

| Table | Purpose |
|-------|---------|
| `books` | Master record per book — title, notes, all status fields |
| `outlines` | Full version history of every outline generated |
| `chapters` | Individual chapter content, summaries, notes, and status |
| `notifications_log` | Audit trail of every notification sent |

---

## Notification Events

| Event | Trigger |
|-------|---------|
| `outline_ready` | Outline generated — editor review needed |
| `outline_regenerated` | Outline revised with editor notes |
| `chapter_ready` | Chapter generated — editor review needed |
| `chapter_regenerated` | Chapter revised with editor notes |
| `waiting_for_notes` | Pipeline paused — editor action required |
| `final_draft_ready` | Book compiled — download links included |
| `pipeline_error` | Something failed — details included |

---

## Project Structure
```
book_generator/
├── fastapi_service/
│   ├── main.py                  # FastAPI app and route registration
│   ├── orchestrator.py          # Pipeline orchestration engine
│   ├── editor_simulator.py      # Automated editor for demo purposes
│   ├── api/
│   │   ├── schemas.py           # Pydantic request/response models
│   │   └── routes/
│   │       ├── input_routes.py
│   │       ├── outline_routes.py
│   │       ├── chapter_routes.py
│   │       └── compile_routes.py
│   ├── core/
│   │   └── config.py            # Environment config via pydantic-settings
│   ├── db/
│   │   └── supabase_client.py   # Supabase read/write helpers
│   ├── services/
│   │   ├── input_parser.py      # Excel parsing and validation
│   │   ├── openai_service.py    # GPT-4o wrapper with retry logic
│   │   ├── outline_service.py   # Outline generation and versioning
│   │   ├── chapter_service.py   # Chapter generation and context chaining
│   │   ├── compilation_service.py # Final book compilation and upload
│   │   └── notification_service.py # Email and Teams notifications
│   └── utils/
│       ├── prompt_builder.py    # All GPT prompt templates
│       ├── docx_builder.py      # Word document generation
│       └── pdf_builder.py       # PDF generation
├── db/
│   └── migrations/
│       └── 001_initial_schema.sql
├── input/
│   └── books_input.xlsx
├── output/                      # Generated .docx and .pdf files
├── tests/
│   ├── test_milestones3.py
│   ├── test_milestones4.py
│   ├── test_milestones5.py
│   ├── test_milestones6.py
│   ├── test_milestones7.py
│   └── test_full_pipeline.py
├── requirements.txt
├── .env.example
└── README.md
```


APP_ENV=development
```
