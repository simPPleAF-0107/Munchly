# Munchly

AI-powered personalized meal planning platform that creates affordable, nutritionally appropriate 7-day meal plans based on your body, health, diet, budget, location, culture, cuisine and the food you actually enjoy.

## Tech Stack

- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: Python + FastAPI + SQLAlchemy 2.0
- **Database**: PostgreSQL
- **AI**: Google Gemini (optional enhancement layer)

## Getting Started

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker & Docker Compose

### Backend
```bash
cd backend
pip install -e ".[dev]"
docker compose up -d db
alembic upgrade head
python -m app.db.init_db  # Seed data
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
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
