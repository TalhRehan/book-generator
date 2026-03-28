from fastapi import FastAPI
from fastapi_service.api.routes.input_routes import router as input_router
from fastapi_service.api.routes.outline_routes import router as outline_router

app = FastAPI(title="Book Generator API")

app.include_router(input_router, prefix="/api")
app.include_router(outline_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}