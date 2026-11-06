"""Native adjacency-list structure for the transport network."""

from app.domain import Connection, Station


class TransportGraph:
    """A directed transport graph stored entirely in memory."""

    __slots__ = ("_adjacency_list",)

    def __init__(self) -> None:
        self._adjacency_list: dict[Station, list[Connection]] = {}

    def add_station(self, station: Station) -> None:
        self._adjacency_list.setdefault(station, [])

    def get_neighbors(self, station: Station) -> list[Connection]:
        return self._adjacency_list[station]
