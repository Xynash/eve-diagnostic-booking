# EVE Healthcare: Diagnostic Booking Service

Backend service for booking diagnostic tests and processing simulated payments. Built with FastAPI, SQLAlchemy and PostgreSQL.

## Running locally

Requires Docker.

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python -m scripts.seed
```

The API runs at `http://localhost:8000` and the Swagger docs are at `http://localhost:8000/docs`.

The seed script adds two centres, three tests and four centre-test prices. Run it once; running it again will create duplicates.

Run the tests (they use an in-memory SQLite database, not Postgres):

```bash
docker compose exec api pytest -v
```

## Project layout

```
app/
  core/       config, db session, JWT + password helpers, auth dependency
  models/     SQLAlchemy models
  schemas/    Pydantic request/response models
  routers/    auth, centres, bookings, payments
scripts/      seed data
tests/        pytest suite
alembic/      migrations
```

## API

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/signup` | no | Create a user |
| POST | `/auth/login` | no | Returns a JWT |
| GET | `/centres/` | no | List centres with their tests and prices |
| GET | `/centres/{id}` | no | One centre |
| POST | `/bookings/` | yes | Create a booking (starts `PENDING`) |
| GET | `/bookings/` | yes | Your bookings |
| GET | `/bookings/{id}` | yes | One of your bookings |
| POST | `/bookings/{id}/cancel` | yes | Cancel a `PENDING` booking |
| POST | `/payments/` | yes | Run a simulated payment for a booking |
| POST | `/payments/webhook/` | no | Payment status update from the provider |

Protected routes expect `Authorization: Bearer <token>`.

### Example requests

```bash
curl -X POST localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'

curl -X POST localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'
# {"access_token": "eyJ...", "token_type": "bearer"}

curl -X POST localhost:8000/bookings/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"centre_test_id": 1, "appointment_time": "2030-01-01T10:00:00"}'

curl -X POST localhost:8000/payments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"booking_id": 1}'
# {"id": 1, "booking_id": 1, "amount": "500.00", "status": "SUCCESS", "transaction_id": "..."}

curl -X POST localhost:8000/payments/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"event_id": "evt_001", "transaction_id": "<transaction_id from above>", "status": "SUCCESS"}'
# first call:  {"detail": "Webhook processed", "booking_status": "CONFIRMED"}
# repeat call: {"detail": "Event already processed", "event_id": "evt_001"}
```

## Database design

- `users`: id, email (unique), hashed_password, created_at
- `centres`: id, name, location
- `tests`: id, name
- `centre_tests`: centre_id, test_id, price. Unique on (centre_id, test_id). Price lives here because the same test can cost different amounts at different centres.
- `bookings`: user_id, centre_test_id, appointment_time, amount, status (`PENDING`, `CONFIRMED`, `FAILED`, `CANCELLED`), created_at
- `payments`: booking_id, amount, status (`SUCCESS`, `FAILED`), transaction_id (unique), created_at
- `webhook_events`: event_id (unique), payload, received_at

A booking points at a `centre_test` row, so the test, the centre and the price are always consistent with each other. `bookings.amount` copies the price at booking time, so later price changes don't rewrite history.

### Webhook idempotency

Every webhook carries an `event_id`. The handler first checks `webhook_events` for it and returns early if it exists. The unique constraint on `event_id` is the real guarantee: if two identical requests race past the check, the second insert fails with an `IntegrityError`, which is caught, rolled back, and treated as an already-processed event. The payment update, booking update and event record are committed in one transaction, so a failed call leaves nothing half-applied and can be retried safely.

## Assumptions

- The payment simulation succeeds about 80% of the time (random). Tests patch this to make it deterministic.
- The webhook endpoint is unauthenticated because it stands in for an external provider.
- The webhook payload identifies the payment by `transaction_id`, and `event_id` is the idempotency key.
- A booking can only be paid while `PENDING`, and only cancelled while `PENDING`.
- Appointment times must be in the future. Times sent without a timezone are treated as UTC.
- Centres and tests are read-only through the API and managed through the seed script.
- JWTs expire after 60 minutes. There are no refresh tokens.
- Users can only see and act on their own bookings (403 otherwise).

## What I'd improve with more time

- Verify a signature on incoming webhooks so only the provider can call them.
- Add a proper booking state machine. Right now a webhook can move a booking to any status, including one that was cancelled.
- Check the webhook amount against the payment amount.
- Lock the booking row during payment so two simultaneous requests can't both pay.
- Admin endpoints for managing centres and tests, plus filtering by location.
- Pagination on list endpoints.
- Structured logging, rate limiting, and a retry queue for webhook processing.
- Run the tests against Postgres in CI instead of SQLite.
- Make the seed script idempotent.