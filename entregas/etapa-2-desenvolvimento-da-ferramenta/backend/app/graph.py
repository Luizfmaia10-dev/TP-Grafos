"""Native adjacency-list structure for the transport network."""

from bisect import bisect_right
from collections.abc import Iterator

from app.domain import Connection, Station, TemporaryVertex


class TransportGraph:
    """A directed transport graph stored entirely in memory."""

    __slots__ = ("_adjacency_list",)

    def __init__(self) -> None:
        self._adjacency_list: dict[Station, list[Connection]] = {}

    def add_station(self, station: Station) -> None:
        self._adjacency_list.setdefault(station, [])

    def add_connection(self, origin: Station, connection: Connection) -> None:
        connections = self._adjacency_list[origin]
        if connection.destination not in self._adjacency_list:
            raise KeyError(connection.destination)
        insertion_index = bisect_right(
            connections,
            connection.departure_time,
            key=lambda item: item.departure_time,
        )
        connections.insert(insertion_index, connection)

    def get_neighbors(self, station: Station) -> list[Connection]:
        return self._adjacency_list[station]

    def iter_stations(self) -> Iterator[Station]:
        """Iterate over registered stations without copying the graph."""
        return iter(self._adjacency_list)

    def remove_temporary_vertex(self, vertex: TemporaryVertex) -> None:
        del self._adjacency_list[vertex]
        for connections in self._adjacency_list.values():
            connections[:] = [
                connection
                for connection in connections
                if connection.destination != vertex
            ]
