from fastapi import FastAPI

app = FastAPI(
    title="Dispatch Dashboard API",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "Dispatch Dashboard API is running!"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}