# FPL Optimizer Backend

FastAPI backend for Fantasy Premier League team optimization and transfer recommendations.

## Features

- **Real FPL Data Integration**: Fetches live player data from official FPL API
- **SQLite Database**: Stores player and team data locally
- **Optimization Engine**: Generates transfer recommendations based on current form and value
- **REST API**: Clean API endpoints for frontend integration
- **Rate Limiting**: Protects against abuse (10 req/min/IP)
- **CORS Enabled**: Configured for frontend domain

## Technology Stack

- **Python 3.9+**
- **FastAPI 0.128.0** - Modern web framework
- **SQLAlchemy 2.0** - ORM for database operations
- **httpx** - Async HTTP client for FPL API
- **slowapi** - Rate limiting middleware
- **Uvicorn** - ASGI server

## Project Structure

```
fpl-optimizer-backend/
├── main.py              # FastAPI app entry point
├── database.py          # SQLAlchemy configuration
├── models.py            # Database models
├── schemas.py           # Pydantic schemas
├── crud.py              # Database operations
├── routers/             # API route handlers
├── services/            # Business logic layer
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variables template
```

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Initialize Database

```bash
# Database will be created automatically on first run
python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine)"
```

### 5. Run Development Server

```bash
uvicorn main:app --reload
```

Server will start at: http://localhost:8000

## API Documentation

Once the server is running:

- **Interactive Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Health Check

```
GET /health
```

Returns API health status.

### Team Fetch (Coming in Story 3.5)

```
GET /api/team/{team_id}
```

Fetches FPL team data for given team ID.

### Optimization (Coming in Story 3.6)

```
POST /api/optimize
Body: {"team_id": 123456}
```

Returns transfer recommendations for the team.

## Database Schema

### Players Table
- Stores FPL player data (name, position, cost, points, form, etc.)
- Updated from FPL API bootstrap-static endpoint

### Teams Table
- Stores Premier League team information
- Includes strength ratings for attack/defence home/away

### Gameweeks Table
- Tracks current and upcoming gameweeks
- Used for fixture-based recommendations

### Sync Metadata Table
- Tracks last successful data sync from FPL API
- Enables graceful degradation when API is unavailable

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
# Format code
black .

# Lint code
flake8 .
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## Deployment

### Railway (Recommended)

1. Create account at railway.app
2. Connect GitHub repository
3. Set environment variables in Railway dashboard
4. Deploy automatically on push to main

### Environment Variables for Production

```
DATABASE_URL=postgresql://...  # Use PostgreSQL for production
FPL_API_BASE_URL=https://fantasy.premierleague.com/api
CORS_ORIGINS=https://fpl-optimizer-frontend.vercel.app
API_RATE_LIMIT=10/minute
```

## FPL API Integration

This backend integrates with the official FPL API:

- **Bootstrap Static**: https://fantasy.premierleague.com/api/bootstrap-static/
  - All players, teams, gameweeks
  - Updated after each gameweek

- **Entry/Team**: https://fantasy.premierleague.com/api/entry/{team_id}/
  - User team information
  - Current squad and bank balance

- **Element Summary**: https://fantasy.premierleague.com/api/element-summary/{player_id}/
  - Player history and fixtures
  - Used for detailed recommendations

## License

MIT

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Support

For issues and questions, please open a GitHub issue.
