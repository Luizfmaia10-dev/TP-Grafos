"""Time-dependent A* routing engine."""

from contextlib import contextmanager
from collections.abc import Iterator
from math import asin, cos, isfinite, radians, sin, sqrt
from uuid import uuid4

from app.domain import Connection, Station, TemporaryVertex, VehicleType
from app.graph import TransportGraph

EARTH_RADIUS_KM = 6371.0
MAX_SNAP_DISTANCE_KM = 0.8
WALKING_SPEED_KM_PER_MINUTE = 5.0 / 60.0


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

    @staticmethod
    def max_speed_of(graph: TransportGraph) -> float:
        """Find the maximum speed (km/min) across all graph edges with positive duration.

        Edges with travel_time <= 0 are ignored to avoid division by zero.
        If the graph has no positive duration edges, returns walking speed.
        """
        max_speed = 0.0
        for station in graph.iter_stations():
            for connection in graph.get_neighbors(station):
                if connection.travel_time > 0:
                    speed = connection.distance / connection.travel_time
                    if speed > max_speed:
                        max_speed = speed
        return max_speed if max_speed > 0.0 else WALKING_SPEED_KM_PER_MINUTE

    def heuristic(self, current: Station, target: Station) -> float:
        distance = haversine(
            current.latitude, current.longitude, target.latitude, target.longitude
        )
        return distance / self.max_speed

    @contextmanager
    def snap_to_network(
        self, latitude: float, longitude: float, marker_type: str
    ) -> Iterator[TemporaryVertex]:
        if marker_type not in {"origin", "destination"}:
            raise ValueError("marker_type must be 'origin' or 'destination'")
        if not (
            isfinite(latitude)
            and -90.0 <= latitude <= 90.0
            and isfinite(longitude)
            and -180.0 <= longitude <= 180.0
        ):
            raise ValueError("latitude and longitude must be valid coordinates")

        nearest_station = None
        nearest_distance = float("inf")
        for station in self.graph.iter_stations():
            if isinstance(station, TemporaryVertex):
                continue
            distance = haversine(
                latitude, longitude, station.latitude, station.longitude
            )
            if distance < nearest_distance:
                nearest_station = station
                nearest_distance = distance

        if nearest_station is None or nearest_distance > MAX_SNAP_DISTANCE_KM:
            raise ValueError("no real station found within 800 metres")

        vertex = TemporaryVertex(
            f"temporary-{uuid4().hex}",
            f"Temporary {marker_type}",
            latitude,
            longitude,
            marker_type,
        )
        self.graph.add_station(vertex)
        try:
            if marker_type == "origin":
                origin, destination = vertex, nearest_station
            else:
                origin, destination = nearest_station, vertex
            connection = Connection(
                "temporary-walk",
                destination,
                VehicleType.WALK,
                nearest_distance / WALKING_SPEED_KM_PER_MINUTE,
                nearest_distance,
                0.0,
            )
            self.graph.add_connection(origin, connection)
            yield vertex
        finally:
            self.graph.remove_temporary_vertex(vertex)
