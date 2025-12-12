## Authentication

### POST `/auth/login`
- Body: `{"username": "...", "password": "..."}`
- Validations:
  - Rate-limit per IP (5/min using Flask-Limiter).
  - Contractor status must be `فعال`.
- Response:
  ```json
  {
    "access_token": "<jwt>",
    "refresh_token": "<jwt>",
    "contractor": {
      "detail_code": "0026968",
      "name": "سیاوش ایوبی",
      "status": "active"
    }
  }
  ```

### POST `/auth/refresh`
- Requires refresh token in Authorization header.
- Returns new access token.

## Contractor Profile

### GET `/me`
- Headers: `Authorization: Bearer <access_token>`
- Response: contractor record and latest summary counts (`total_invoices`, `pending_amount`, etc.).

## Invoice APIs

### GET `/invoices`
- Query params:
  - `status` (multi-valued)
  - `from_date`, `to_date` (Jalali or ISO, backend converts)
  - `cover_number`, `search` (matches supplier name, automation number)
  - `page`, `page_size`
- Returns paginated list merging summary/detail tables.
- Sample payload:
  ```json
  {
    "page": 1,
    "page_size": 20,
    "total": 125,
    "items": [
      {
        "cover_number": "71435",
        "automation_number": "14010010",
        "invoice_date": "2023-12-03",
        "status_summary": "تاييد شده",
        "gross_amount_summary": 1084877000,
        "detail_count": 2,
        "detail_statuses": ["ثبت شده", "معلق"]
      }
    ]
  }
  ```

### GET `/invoices/<cover_number>`
- Response merges:
  - Summary row (single).
  - Array of detail rows filtered by `detail_code`.
  ```json
  {
    "summary": {...},
    "details": [...]
  }
  ```

### GET `/invoices/<cover_number>/export`
- Optional: return Excel/PDF for single cover.

## Upload APIs (Admin)

### POST `/admin/uploads`
- Multipart form with fields: `contractors_file`, `summary_file`, `detail_file`.
- Kicks off background import job.

### GET `/admin/uploads/<batch_id>`
- Returns processing status, counts, error list.

## Middleware & Utilities
- JWT auth middleware to fetch contractor by token, verify active status, and inject `detail_code`.
- Pagination helper consistent across endpoints.
- Error responses use structure: `{"error": {"code": "validation_error", "message": "...", "details": [...]}}`.

## Testing Checklist
- Unit tests for each endpoint:
  - Auth success/failure.
  - Invoice listing filters.
  - Permission enforcement (contractor cannot see others' data).
- Integration tests with seeded data verifying merges of summary/detail tables.







