"""HTTP request and response models, separate from the graph domain."""

from dataclasses import dataclass
from datetime import date
import re
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator, model_validator

from app.domain import Station, VehicleType
from app.time_utils import TimeUtils

StationId = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]
DEPARTURE_TIME_PATTERN = re.compile(r"[0-9]{2,}:[0-5][0-9]")


class AddressPoint(BaseModel):
    """One user-selected address with coordinates and a walking limit."""

    model_config = ConfigDict(extra="forbid")

    label: Annotated[
        str,
        StringConstraints(strict=True, strip_whitespace=True, min_length=1),
    ]
    latitude: float
    longitude: float
    max_walk_meters: int
    station_id: StationId | None = None


class RouteSearchRequest(BaseModel):
    """A station or address search within the loaded GTFS service day."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["station", "address"] = "station"
    origin_id: StationId | None = None
    destination_id: StationId | None = None
    origin: AddressPoint | None = None
    destination: AddressPoint | None = None
    departure_time: str

    @field_validator("departure_time")
    @classmethod
    def validate_departure_time(cls, value: str) -> str:
        if not isinstance(value, str) or DEPARTURE_TIME_PATTERN.fullmatch(value) is None:
            raise ValueError("Departure time must use HH:MM without seconds")
        try:
            TimeUtils.time_to_minutes(f"{value}:00")
        except OverflowError:
            raise ValueError("Departure time is outside the supported range") from None
        return value

    @model_validator(mode="after")
    def validate_search_mode(self) -> Self:
        if self.mode == "station":
            if self.origin_id is None or self.destination_id is None:
                raise ValueError("Station searches require origin_id and destination_id")
            if self.origin_id == self.destination_id:
                raise ValueError("Origin and destination must be different stations")
        else:
            if self.origin is None or self.destination is None:
                raise ValueError("Address searches require origin and destination")
            if self.origin.station_id is None:
                raise ValueError("Address searches require the selected origin station")
        return self


@dataclass(frozen=True, slots=True)
class RouteStep:
    """One graph connection with absolute timestamps and rounded costs."""

    origin: Station
    destination: Station
    route_id: str
    route_short_name: str
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
    instructions: list[str]


@dataclass(frozen=True, slots=True)
class RouteSearchResponse:
    status: Literal["found", "no-route"]
    service_date: date
    origin: Station
    destination: Station
    departure_time: str
    route: RouteResult | None
