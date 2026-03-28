"""FastAPI route handlers for this API module."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi_service.services.compilation_service import compile_book

router = APIRouter()


class CompileRequest(BaseModel):
    book_id: str


@router.post("/compile")
def compile(req: CompileRequest):
    """Compile."""
    try:
        result = compile_book(req.book_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))