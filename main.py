"""
FPL Optimizer API - Main Application Entry Point

FastAPI backend for FPL team optimization and recommendations.
Integrates with official FPL API to fetch real player data.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="FPL Optimizer API",
    description="Backend API for Fantasy Premier League team optimization and transfer recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    """
    Health check endpoint for monitoring.

    Returns:
        dict: Status of the API
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "FPL Optimizer API"
    }

@app.get("/")
async def root():
    """
    Root endpoint with API information.

    Returns:
        dict: API welcome message and documentation links
    """
    return {
        "message": "FPL Optimizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/init-db")
async def initialize_database():
    """
    TEMPORARY endpoint to initialize database tables.

    This endpoint should be called once after deployment to create all database tables.
    Remove this endpoint after successful initialization for security.

    Returns:
        dict: Success or error message
    """
    try:
        from database import engine
        from models import Base
        Base.metadata.create_all(bind=engine)
        return {
            "status": "success",
            "message": "Database tables created successfully!",
            "note": "REMOVE THIS ENDPOINT after initialization for security"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating database tables: {str(e)}"
        }

# Import routers
from routers import team, optimize
app.include_router(team.router, prefix="/api", tags=["team"])
app.include_router(optimize.router, prefix="/api", tags=["optimize"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
