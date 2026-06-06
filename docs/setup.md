## Environment Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 15

### Backend (Flask)
1. Create a virtual environment:
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy the environment template and fill required variables:
   ```powershell
   copy config.example.env .env
   ```

   Required variables:

   | Variable | Requirement |
   |----------|-------------|
   | `DATABASE_URL` | PostgreSQL SQLAlchemy URL, for example `postgresql+psycopg://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>`. |
   | `SECRET_KEY` | Strong random value, at least 32 characters. |
   | `JWT_SECRET_KEY` | Strong random value, at least 32 characters. |
   | `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed browser origins. |

   Generate secrets locally:
   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Never commit `.env` or real connection strings. Use a secret manager for production.

3. Initialise or upgrade the database:
   ```powershell
   flask db upgrade
   ```

4. Run the API:
   ```powershell
   flask run --port <API_PORT>
   ```

### Frontend (React + Vite)
1. Install dependencies:
   ```powershell
   cd ..\frontend
   npm install
   ```

2. If the API is not on the default local address, create a local `.env`:
   ```text
   VITE_API_BASE_URL=http://<API_HOST>:<API_PORT>
   ```

3. Start the dev server:
   ```powershell
   npm run dev -- --port <FRONTEND_PORT>
   ```

### Useful Commands
- Frontend lint and build:
  ```powershell
  npm run lint
  npm run build
  ```

- Backend tests:
  ```powershell
  pytest
  ```
