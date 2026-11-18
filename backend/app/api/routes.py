"""Time-dependent route searches exposed as REST requests."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.route_models import (
    RouteResult,
    RouteSearchRequest,
    RouteSearchResponse,
    RouteStep,
)
from app.domain import Connection, Station
from app.itinerary import Itinerary
from app.network import RouteNetwork, get_network
from app.route_simulator import RouteSimulator
from app.time_utils import TimeUtils

router = APIRouter(prefix="/routes", tags=["routes"])


def build_route_result(path: list[tuple[Station, Connection]], departure_time: float) -> RouteResult:
    """Adapt domain itinerary costs to the existing HTTP response contract."""
    if not path:
        return RouteResult(TimeUtils.minutes_to_time(departure_time), 0, 0, 0, 0, [])
    itinerary = Itinerary(path[0][0], departure_time, path)
    return RouteResult(
        arrival_time=itinerary.arrival_time,
        total_seconds=itinerary.total_seconds,
        waiting_seconds=itinerary.waiting_seconds,
        travel_seconds=itinerary.travel_seconds,
        distance_km=itinerary.distance_km,
        steps=[RouteStep(
            origin=step.origin, destination=step.destination,
            route_id=step.route_id, vehicle_type=step.vehicle_type,
            departure_time=step.departure_time, arrival_time=step.arrival_time,
            waiting_seconds=step.waiting_seconds, travel_seconds=step.travel_seconds,
            distance_km=step.distance_km,
        ) for step in itinerary.steps],
    )


@router.post(
    "/search",
    response_model=RouteSearchResponse,
    responses={
        404: {"description": "Unknown origin or destination station"},
        503: {"description": "Transport network is not configured"},
    },
)
def search_route(
    query: RouteSearchRequest,
    network: Annotated[RouteNetwork, Depends(get_network)],
) -> RouteSearchResponse:
    """Find the earliest arrival using the shared graph for its configured date."""
    for field, station_id in (("origin_id", query.origin_id), ("destination_id", query.destination_id)):
        if station_id not in network.stations:
            raise HTTPException(404, detail={"code": "unknown_station", "field": field})
    origin = network.stations[query.origin_id]
    destination = network.stations[query.destination_id]
    departure_time = TimeUtils.time_to_minutes(query.departure_time)
    simulator = RouteSimulator(network.graph, network.max_speed)
    path = simulator.calculate_route(origin, destination, departure_time)
    return RouteSearchResponse(
        status="no-route" if path is None else "found",
        service_date=network.service_date,
        origin=origin,
        destination=destination,
        departure_time=query.departure_time,
        route=None if path is None else build_route_result(path, departure_time),
    )
