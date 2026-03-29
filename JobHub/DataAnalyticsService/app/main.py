from fastapi import FastAPI

app = FastAPI(title="Data Analytics Service (Base)")

@app.get("/")
def read_root():
    return {"message": "Data Analytics Service is running!"}
