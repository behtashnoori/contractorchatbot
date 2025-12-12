## Environment Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 15 (optional for production; SQLite works for local dev)

### Backend (Flask)
1. Create virtual environment:
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy environment template:
   ```powershell
   copy config.example.env .env
   ```
   Populate with secrets:
   ```
   FLASK_APP=wsgi.py
   FLASK_ENV=development
   SECRET_KEY=change-me
   JWT_SECRET_KEY=change-me-asap
   DATABASE_URL=sqlite:///instance/app.db
   ```
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







