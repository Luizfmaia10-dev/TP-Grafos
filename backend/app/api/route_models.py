"""HTTP request and response models, separate from the graph domain."""

from dataclasses import dataclass
from datetime import date
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator, model_validator

from app.domain import Station, VehicleType
from app.time_utils import TimeUtils

StationId = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]


class RouteSearchRequest(BaseModel):
    """Station IDs and a timestamp within the loaded GTFS service day."""

    model_config = ConfigDict(extra="forbid")

    origin_id: StationId
    destination_id: StationId
    departure_time: str

    @field_validator("departure_time")
    @classmethod
    def validate_departure_time(cls, value: str) -> str:
        try:
            TimeUtils.time_to_minutes(value)
        except OverflowError:
            raise ValueError("Departure time is outside the supported range") from None
        return value

    @model_validator(mode="after")
    def validate_distinct_stations(self) -> Self:
        if self.origin_id == self.destination_id:
            raise ValueError("Origin and destination must be different stations")
        return self


@dataclass(frozen=True, slots=True)
class RouteStep:
    """One graph connection with absolute timestamps and rounded costs."""

    origin: Station
    destination: Station
    route_id: str
    vehicle_type: VehicleType
    departure_time: str
    arrival_time: str
    waiting_seconds: int
    travel_seconds: int
    distance_km: float


@dataclass(frozen=True, slots=True)
class RouteResult:
    """API representation of the path; durations include every travel mode."""

    arrival_time: str
    total_seconds: int
    waiting_seconds: int
    travel_seconds: int
    distance_km: float
    steps: list[RouteStep]


@dataclass(frozen=True, slots=True)
class RouteSearchResponse:
    status: Literal["found", "no-route"]
    service_date: date
    origin: Station
    destination: Station
    departure_time: str
    route: RouteResult | None
