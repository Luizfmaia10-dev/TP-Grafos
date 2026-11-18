"""Time-dependent route searches exposed as REST requests."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.route_models import RouteResult, RouteSearchRequest, RouteSearchResponse, RouteStep
from app.domain import Connection, Station, VehicleType
from app.network import RouteNetwork, get_network
from app.route_simulator import RouteSimulator
from app.time_utils import TimeUtils

router = APIRouter(prefix="/routes", tags=["routes"])


def build_route_result(path: list[tuple[Station, Connection]], departure_time: float) -> RouteResult:
    """Round absolute timestamps first so all reported durations stay additive."""
    current_time = departure_time
    steps = []
    for origin, connection in path:
        departure = (
            current_time if connection.vehicle_type is VehicleType.WALK
            else connection.departure_time
        )
        arrival = departure + connection.travel_time
        departure_seconds = round(departure * 60)
        arrival_seconds = round(arrival * 60)
        steps.append(RouteStep(
            origin=origin,
            destination=connection.destination,
            route_id=connection.route_id,
            vehicle_type=connection.vehicle_type,
            departure_time=TimeUtils.minutes_to_time(departure),
            arrival_time=TimeUtils.minutes_to_time(arrival),
            waiting_seconds=departure_seconds - round(current_time * 60),
            travel_seconds=arrival_seconds - departure_seconds,
            distance_km=connection.distance,
        ))
        current_time = arrival

    return RouteResult(
        arrival_time=TimeUtils.minutes_to_time(current_time),
        total_seconds=round(current_time * 60) - round(departure_time * 60),
        waiting_seconds=sum(step.waiting_seconds for step in steps),
        travel_seconds=sum(step.travel_seconds for step in steps),
        distance_km=sum(step.distance_km for step in steps),
        steps=steps,
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
