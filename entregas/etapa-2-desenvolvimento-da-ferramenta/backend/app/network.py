"""Shared service-day network and API dependency."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from fastapi import HTTPException, Request

from app.data_loader import DataLoader
from app.domain import Station
from app.graph import TransportGraph
from app.route_simulator import RouteSimulator


@dataclass(frozen=True, slots=True)
class RouteNetwork:
    """Keep one graph and its lookup data for a specific GTFS service day."""

    graph: TransportGraph
    stations: dict[str, Station]
    max_speed: float
    service_date: date

    @classmethod
    def load(cls, data_directory: Path, service_date: date) -> "RouteNetwork":
        graph = DataLoader(data_directory, service_date=service_date).build_graph()
        return cls(
            graph=graph,
            stations={station.station_id: station for station in graph.iter_stations()},
            max_speed=RouteSimulator.max_speed_of(graph),
            service_date=service_date,
        )


def get_network(request: Request) -> RouteNetwork:
    """Reject transport queries when no service-day network is configured."""
    network = request.app.state.network
    if network is None:
        raise HTTPException(status_code=503, detail="Transport network is not configured")
    return network
