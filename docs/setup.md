## Environment Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 15 (required; use a local or remote instance and set `DATABASE_URL`)

### Backend (Flask)
1. Create virtual environment:
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy environment template and fill **required** variables (the backend exits on startup if any are missing, empty, or unsafe):

   | Variable | Requirement |
   |----------|-------------|
   | `DATABASE_URL` | Non-empty PostgreSQL SQLAlchemy URL (`postgresql+psycopg://…`). |
   | `SECRET_KEY` | Non-empty, at least 32 characters, not a known placeholder (e.g. not `change-me`). |
   | `JWT_SECRET_KEY` | Same as `SECRET_KEY`; you may use `JWT_SECRET` instead as an alias. |
   | `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed origins (at least one); used for CORS and error-handler origins. |

   ```powershell
   copy config.example.env .env
   ```

   Replace the long example secrets in `.env` with strong random values (e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"`).

   Production: set `FLASK_ENV=production` and `FLASK_DEBUG=0` (DEBUG must be off).
3. Initialise database:
   ```powershell
   flask db init
   flask db migrate -m "Initial tables"
   flask db upgrade
   ```
4. Run the API:
   ```powershell
   flask run --port 5000
   ```

### Frontend (React + Vite)
1. Install dependencies:
   ```powershell
   cd ..\frontend
   npm install
   ```
2. Create `.env`:
   ```
   VITE_API_BASE_URL=http://localhost:5000
   ```
3. Start dev server:
   ```powershell
   npm run dev -- --port 5173
   ```

### Useful Commands
- Format lint (frontend):
  ```powershell
  npm run lint
  npm run build
  ```
- Run backend tests (placeholder):
  ```powershell
  pytest
  ```







