from fastapi import FastAPI
from app.core.config import settings
from app.api.endpoints import cv_scoring

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/openapi.json"
)

app.include_router(cv_scoring.router, prefix="/api/v1/ai", tags=["cv-intelligence"])

@app.on_event("startup")
async def startup_event():
    print("Loading AI Models into memory...")
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
