from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi_service.services.outline_service import generate_outline, regenerate_outline

router = APIRouter()


class OutlineRequest(BaseModel):
    book_id: str


@router.post("/outline/generate")
def generate(req: OutlineRequest):
    try:
        result = generate_outline(req.book_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/outline/regenerate")
def regenerate(req: OutlineRequest):
    try:
        result = regenerate_outline(req.book_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))