from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="CV Intelligence Service",
    description="AI service phân tích CV, đề xuất công việc phù hợp",
    version="1.0.0",
    root_path="/api/v1/cv"
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "CVIntelligenceService", "port": 5006}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5006, reload=True)
