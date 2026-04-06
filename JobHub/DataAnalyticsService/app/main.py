from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="Data Analytics Service",
    description="AI service phân tích dữ liệu tuyển dụng, xu hướng nghề nghiệp",
    version="1.0.0",
    root_path="/api/v1/analytics"
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "DataAnalyticsService", "port": 5007}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5007, reload=True)
