# Munchly

AI-powered personalized meal planning platform that creates affordable, nutritionally appropriate 7-day meal plans based on your body, health, diet, budget, location, culture, cuisine and the food you actually enjoy.

## Tech Stack

- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: Python + FastAPI + SQLAlchemy 2.0
- **Database**: PostgreSQL
- **AI**: Google Gemini (optional enhancement layer)

## Getting Started

All dependencies install **inside the project folder** — nothing goes to your C drive.

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker & Docker Compose

### Backend
```bash
cd backend

# Create & activate virtual environment (stays in backend/.venv/)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies into .venv (not global)
pip install -e ".[dev]"

# Start database
docker compose up -d

# Run migrations & seed data
alembic upgrade head
python -m app.db.init_db

# Start API server
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend

# Install dependencies (node_modules/ stays local, npm cache in .npm-cache/)
npm install

# Start dev server
npm run dev
```

## Architecture

```
AI Layer (optional — app works without it)
    ↓
Recommendation Layer (scoring / optimization)
    ↓
Safety + Data Layer (nutrition / allergies / diet / medical rules / prices)
```

AI can never bypass the Safety + Data layer.

## License
MIT
