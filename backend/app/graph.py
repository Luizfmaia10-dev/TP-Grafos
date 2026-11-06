"""Native adjacency-list structure for the transport network."""

from app.domain import Connection, Station


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
        connections.append(connection)

    def get_neighbors(self, station: Station) -> list[Connection]:
        return self._adjacency_list[station]
