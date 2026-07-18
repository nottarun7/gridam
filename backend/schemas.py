from typing import Any

from pydantic import BaseModel, Field

from config import KOCHI


class ScoreRequest(BaseModel):
    stations: list[dict[str, Any]]
    lat: float = KOCHI["lat"]
    lng: float = KOCHI["lng"]
    mode: str = "balanced"


class RouteRequest(BaseModel):
    start: dict[str, float]
    end: dict[str, float]


class StationCreate(BaseModel):
    name: str
    lat: float
    lng: float
    operator: str = "Community"
    connector: str = "Type 2"
    power_kw: float = Field(default=22, gt=0)


class SessionCreate(BaseModel):
    station_id: str
    station_name: str = "Selected charger"
    kwh: float = Field(default=18, ge=0)
    carbon_intensity: float = Field(default=520, ge=0)
    cost_inr: float = Field(default=144, ge=0)


class ChatRequest(BaseModel):
    message: str
    context: dict[str, Any] = Field(default_factory=dict)
