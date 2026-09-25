from fastapi import FastAPI

app = FastAPI(title="EVE Healthcare Booking Service")


@app.get("/health")
def health_check():
    return {"status": "ok"}