"""
Pydantic Schemas

Request/response models for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PlayerBase(BaseModel):
    """Base player schema with common fields."""
    id: int
    web_name: str
    position: int
    team_name: str
    now_cost: int
    total_points: int
    points_per_game: float
    form: float


class PlayerResponse(PlayerBase):
    """Player response schema with additional details."""
    first_name: Optional[str] = None
    second_name: Optional[str] = None
    team_id: int
    selected_by_percent: float
    minutes: int
    goals_scored: int
    assists: int
    clean_sheets: int
    bonus: int

    class Config:
        from_attributes = True


class TransferRecommendation(BaseModel):
    """Transfer recommendation schema."""
    playerOut: PlayerBase
    playerIn: PlayerBase
    rationale: str
    cost_change: int


class OptimizationRequest(BaseModel):
    """Request schema for optimization endpoint."""
    team_id: int = Field(..., gt=0, description="FPL team ID")


class OptimizationResponse(BaseModel):
    """Response schema for optimization endpoint."""
    recommendations: List[TransferRecommendation]
    computationTime: float = Field(..., description="Time taken in milliseconds")


class TeamResponse(BaseModel):
    """Response schema for team fetch endpoint."""
    team_id: int
    players: List[PlayerBase]
    team_value: float = Field(..., description="Total team value in millions")
    total_points: int


class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str
    version: str
    service: str
    database_status: Optional[str] = None
    fpl_api_status: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
