"""Time-dependent A* routing engine."""

from bisect import bisect_left
from contextlib import contextmanager
from collections.abc import Iterator
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from math import asin, cos, isfinite, radians, sin, sqrt
from uuid import uuid4

from app.domain import Connection, Station, TemporaryVertex, VehicleType
from app.graph import TransportGraph

EARTH_RADIUS_KM = 6371.0
MIN_SNAP_DISTANCE_KM = 0.1
MAX_SNAP_DISTANCE_KM = 2.0
DEFAULT_SNAP_DISTANCE_KM = 0.8
WALKING_SPEED_KM_PER_MINUTE = 5.0 / 60.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = radians(lat1), radians(lat2)
    delta_phi = phi2 - phi1
    delta_lambda = radians(lon2 - lon1)
    a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


@dataclass(frozen=True, slots=True)
class SnapCandidate:
    station: Station
    distance_km: float


class RouteSimulator:
    """Searches the fastest route over a time-dependent transport graph."""

    __slots__ = (
        "graph",
        "max_speed",
        "last_expanded_count",
        "_temporary_connections",
    )

    def __init__(self, graph: TransportGraph, max_speed: float) -> None:
        self.graph = graph
        self.max_speed = max_speed  # km/min, must bound every edge speed
        self.last_expanded_count: int = 0
        self._temporary_connections: dict[Station, list[Connection]] = {}

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

    def calculate_route(
        self, origin: Station, destination: Station, departure_time: float
    ) -> list[tuple[Station, Connection]] | None:
        """Find the earliest arrival route from origin to destination."""
        if origin == destination:
            return []

        g: dict[Station, float] = {origin: departure_time}
        predecessor: dict[Station, tuple[Station, Connection]] = {}
        closed: set[Station] = set()
        counter = count()
        heap: list[tuple[float, int, Station]] = [
            (departure_time + self.heuristic(origin, destination), next(counter), origin)
        ]
        self.last_expanded_count = 0

        while heap:
            _, _, station = heappop(heap)
            if station in closed:
                continue
            self.last_expanded_count += 1
            if station == destination:
                return self._reconstruct_path(predecessor, origin, destination)
            closed.add(station)

            t = g[station]
            connections = self._neighbors(station)

            # 1. Walk connections: on-demand, departing immediately at t
            # Walk connections have departure_time == 0.0 and appear at the prefix of connections.
            for connection in connections:
                if connection.departure_time > 0.0:
                    break
                if connection.vehicle_type is VehicleType.WALK:
                    arrival = t + connection.travel_time
                    if arrival < g.get(connection.destination, float("inf")):
                        g[connection.destination] = arrival
                        predecessor[connection.destination] = (station, connection)
                        heappush(
                            heap,
                            (
                                arrival + self.heuristic(connection.destination, destination),
                                next(counter),
                                connection.destination,
                            ),
                        )

            # 2. Scheduled transit connections: departing at or after t
            start = bisect_left(connections, t, key=lambda c: c.departure_time)
            for i in range(start, len(connections)):
                connection = connections[i]
                if connection.vehicle_type is VehicleType.WALK:
                    continue
                if connection.departure_time >= g.get(destination, float("inf")):
                    break
                arrival = connection.departure_time + connection.travel_time
                if arrival < g.get(connection.destination, float("inf")):
                    g[connection.destination] = arrival
                    predecessor[connection.destination] = (station, connection)
                    heappush(
                        heap,
                        (
                            arrival + self.heuristic(connection.destination, destination),
                            next(counter),
                            connection.destination,
                        ),
                    )

        return None

    def _neighbors(self, station: Station) -> list[Connection]:
        try:
            graph_connections = self.graph.get_neighbors(station)
        except KeyError:
            graph_connections = []
        temporary_connections = self._temporary_connections.get(station, [])
        if not temporary_connections:
            return graph_connections
        return sorted(
            [*temporary_connections, *graph_connections],
            key=lambda connection: connection.departure_time,
        )

    def _reconstruct_path(
        self,
        predecessor: dict[Station, tuple[Station, Connection]],
        origin: Station,
        destination: Station,
    ) -> list[tuple[Station, Connection]]:
        path: list[tuple[Station, Connection]] = []
        current = destination
        while current != origin:
            previous_station, connection = predecessor[current]
            path.append((previous_station, connection))
            current = previous_station
        path.reverse()
        return path

    @contextmanager
    def snap_to_network(
        self,
        latitude: float,
        longitude: float,
        marker_type: str,
        max_distance_km: float = DEFAULT_SNAP_DISTANCE_KM,
        station_id: str | None = None,
        label: str | None = None,
    ) -> Iterator[TemporaryVertex]:
        if marker_type not in {"origin", "destination"}:
            raise ValueError("marker_type must be 'origin' or 'destination'")
        candidates = self.find_snap_candidates(
            latitude, longitude, max_distance_km
        )
        if not candidates:
            raise ValueError("no real station found within the walking limit")
        if station_id is None:
            selected = candidates[0]
        else:
            selected = next(
                (
                    candidate
                    for candidate in candidates
                    if candidate.station.station_id == station_id
                ),
                None,
            )
            if selected is None:
                raise ValueError("selected station is not within the walking limit")

        vertex = TemporaryVertex(
            f"temporary-{uuid4().hex}",
            label or f"Temporary {marker_type}",
            latitude,
            longitude,
            marker_type,
        )
        if marker_type == "origin":
            origin, destination = vertex, selected.station
        else:
            origin, destination = selected.station, vertex
        connection = Connection(
            "temporary-walk",
            destination,
            VehicleType.WALK,
            selected.distance_km / WALKING_SPEED_KM_PER_MINUTE,
            selected.distance_km,
            0.0,
        )
        connections = self._temporary_connections.setdefault(origin, [])
        connections.append(connection)
        try:
            yield vertex
        finally:
            connections.remove(connection)
            if not connections:
                del self._temporary_connections[origin]

    def find_snap_candidates(
        self, latitude: float, longitude: float, max_distance_km: float
    ) -> list[SnapCandidate]:
        self._validate_snap_input(latitude, longitude, max_distance_km)
        candidates = []
        for station in self.graph.iter_stations():
            if isinstance(station, TemporaryVertex):
                continue
            distance = haversine(
                latitude, longitude, station.latitude, station.longitude
            )
            if distance <= max_distance_km:
                candidates.append(SnapCandidate(station, distance))
        return sorted(
            candidates,
            key=lambda candidate: (
                candidate.distance_km,
                candidate.station.station_id,
            ),
        )

    @staticmethod
    def _validate_snap_input(
        latitude: float, longitude: float, max_distance_km: float
    ) -> None:
        if not (
            isfinite(latitude)
            and -90.0 <= latitude <= 90.0
            and isfinite(longitude)
            and -180.0 <= longitude <= 180.0
        ):
            raise ValueError("latitude and longitude must be valid coordinates")
        if not (
            isfinite(max_distance_km)
            and MIN_SNAP_DISTANCE_KM <= max_distance_km <= MAX_SNAP_DISTANCE_KM
        ):
            raise ValueError("max distance must be between 0.1 and 2.0 kilometres")
