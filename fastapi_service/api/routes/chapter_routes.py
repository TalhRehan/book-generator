"""FastAPI route handlers for this API module."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi_service.services.chapter_service import generate_all_chapters, regenerate_chapter

router = APIRouter()


class GenerateChaptersRequest(BaseModel):
    book_id: str


class RegenerateChapterRequest(BaseModel):
    book_id: str
    chapter_id: str


@router.post("/chapters/generate")
def generate(req: GenerateChaptersRequest):
    """Generate."""
    try:
        result = generate_all_chapters(req.book_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/chapters/regenerate")
def regenerate(req: RegenerateChapterRequest):
    """Regenerate."""
    try:
        result = regenerate_chapter(req.book_id, req.chapter_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))