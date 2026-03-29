from fastapi import FastAPI

app = FastAPI(title="CV Intelligence Service (Base)")

@app.get("/")
def read_root():
    return {"message": "CV Intelligence Service is running!"}
