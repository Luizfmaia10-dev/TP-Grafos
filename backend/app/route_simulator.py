"""Time-dependent A* routing engine."""

from math import asin, cos, radians, sin, sqrt

from app.domain import Station
from app.graph import TransportGraph

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = radians(lat1), radians(lat2)
    delta_phi = phi2 - phi1
    delta_lambda = radians(lon2 - lon1)
    a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


class RouteSimulator:
    """Searches the fastest route over a time-dependent transport graph."""

    __slots__ = ("graph", "max_speed")

    def __init__(self, graph: TransportGraph, max_speed: float) -> None:
        self.graph = graph
        self.max_speed = max_speed  # km/min, must bound every edge speed

    def heuristic(self, current: Station, target: Station) -> float:
        distance = haversine(
            current.latitude, current.longitude, target.latitude, target.longitude
        )
        return distance / self.max_speed