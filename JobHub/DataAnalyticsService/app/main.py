from fastapi import FastAPI
from app.api.endpoints import analytics

app = FastAPI(
    title="Data Analytics Service",
    openapi_url="/openapi.json"
)

app.include_router(analytics.router, prefix="/api/v1/ai/analytics", tags=["analytics"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
