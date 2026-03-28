# Automated Book Generation System

A modular system that accepts a book title, generates an outline, writes chapters with context chaining, and compiles a final draft with human-in-the-loop review.

---

## Tech Stack

| Component         | Tool                        |
|-------------------|-----------------------------|
| Automation Engine | Python Orchestrator         |
| Backend API       | FastAPI (Python)            |
| Database          | Supabase (PostgreSQL)       |
| AI Model          | OpenAI GPT-4o               |
| Input Source      | Excel (.xlsx)               |
| Notifications     | SMTP Email + MS Teams       |
| Output Files      | .docx, .pdf, Supabase Storage |

---

## Running the System

### Start API Server
```bash
uvicorn fastapi_service.main:app --reload
```

### Start Orchestrator (separate terminal)
```bash
python -m fastapi_service.orchestrator
```

The orchestrator polls every 60 seconds and automatically:
- Loads new books from Excel into Supabase
- Generates outlines for pending books
- Generates chapters once outline is approved
- Regenerates chapters when editor adds notes
- Compiles final book when all chapters are approved

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/parse-input` | Parse Excel and insert books |
| POST | `/api/outline/generate` | Generate outline for a book |
| POST | `/api/outline/regenerate` | Regenerate outline with new notes |
| POST | `/api/chapters/generate` | Generate all chapters |
| POST | `/api/chapters/regenerate` | Regenerate a single chapter |
| POST | `/api/compile` | Compile final .docx and .pdf |
| GET | `/health` | Health check |

---

## Project Structure

```text
book_generator/
+-- fastapi_service/
¦   +-- orchestrator.py
¦   +-- main.py
¦   +-- api/
¦   +-- core/
¦   +-- db/
¦   +-- services/
¦   +-- utils/
+-- db/
+-- input/
+-- output/
+-- tests/
+-- Dockerfile
+-- docker-compose.yml
+-- requirements.txt
+-- .env
+-- .env.example
```