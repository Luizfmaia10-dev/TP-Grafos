"""Base entities for the in-memory transport graph."""

from dataclasses import dataclass
from enum import Enum


class VehicleType(Enum):
    BUS = "BUS"
    SUBWAY = "SUBWAY"
    WALK = "WALK"


@dataclass(frozen=True, eq=False)
class Station:
    """A station identified by its ID, with coordinates in decimal degrees."""

    station_id: str
    name: str
    latitude: float
    longitude: float

    def __hash__(self) -> int:
        return hash(self.station_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Station):
            return NotImplemented
        return self.station_id == other.station_id


@dataclass
class Connection:
    """A directed trip to a station.

    Travel time is in minutes and distance is in kilometers. Departure time is
    in minutes since the service day's start and may exceed 1440 for late trips.
    """

    route_id: str
    destination: Station
    vehicle_type: VehicleType
    travel_time: float
    distance: float
    departure_time: float
