"""Pydantic request/response models."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class StationIn(BaseModel):
    name: str = Field(..., min_length=1)
    lat: float
    lng: float
    connector: str = "Type 2"


class ScoreCandidate(BaseModel):
    station_id: str
    name: str
    lat: float
    lng: float
    availability: float = 0.5  # 0-1 share of chargers free


class ScoreRequest(BaseModel):
    user_lat: float
    user_lng: float
    mode: Literal["fastest", "greenest", "balanced"] = "balanced"
    candidates: list[ScoreCandidate]


class SessionIn(BaseModel):
    station_id: str
    station_name: str = "Charging session"
    kwh: float = Field(..., gt=0, le=350)


class RouteRequest(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float


class GridBatchRequest(BaseModel):
    station_ids: list[str]


class ProfileIn(BaseModel):
    name: Optional[str] = None
    vehicle: Optional[str] = None
    battery_kwh: Optional[float] = None
    efficiency_km_kwh: Optional[float] = None
    mileage_kmpl: Optional[float] = None
    petrol_price: Optional[float] = None
    tariff: Optional[float] = None
    connector_pref: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    context: dict = {}
