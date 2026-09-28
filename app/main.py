from fastapi import FastAPI

from app.routers import auth, bookings, centres, diagnostic_tests, payments

app = FastAPI(title="EVE Healthcare Booking Service")

app.include_router(auth.router)
app.include_router(centres.router)
app.include_router(diagnostic_tests.router)
app.include_router(bookings.router)
app.include_router(payments.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
