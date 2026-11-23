"""Snap-to-network preview endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from app.domain import Station
from app.network import RouteNetwork, get_network
from app.route_simulator import MAX_SNAP_DISTANCE_KM, RouteSimulator, SnapCandidate

MIN_WALK_METERS = 100
MAX_WALK_METERS = 2_000

router = APIRouter(prefix="/snap", tags=["snap"])


class SnapCandidatesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float
    longitude: float
    max_walk_meters: int


class SnapCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    station: Station
    distance_meters: int


class SnapCandidatesResponse(BaseModel):
    minimum_distance_meters: int
    count: int
    candidates: list[SnapCandidateResponse]


def validate_walk_limit(max_walk_meters: int) -> None:
    if not MIN_WALK_METERS <= max_walk_meters <= MAX_WALK_METERS:
        raise HTTPException(
            status_code=422,
            detail={"code": "snap_distance_out_of_range"},
        )


def candidates_within_limit(
    network: RouteNetwork,
    latitude: float,
    longitude: float,
    max_walk_meters: int,
    *,
    field: str | None = None,
) -> list[SnapCandidate]:
    validate_walk_limit(max_walk_meters)
    simulator = RouteSimulator(network.graph, network.max_speed)
    try:
        available = simulator.find_snap_candidates(
            latitude,
            longitude,
            MAX_SNAP_DISTANCE_KM,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_coordinates", **({"field": field} if field else {})},
        ) from error
    max_distance_km = max_walk_meters / 1_000
    candidates = [
        candidate
        for candidate in available
        if candidate.distance_km <= max_distance_km
    ]
    if candidates:
        return candidates
    detail = {
        "code": "no_station_within_limit",
        "minimum_distance_meters": (
            round(available[0].distance_km * 1_000) if available else None
        ),
    }
    if field:
        detail["field"] = field
    raise HTTPException(status_code=404, detail=detail)


@router.post("/candidates", response_model=SnapCandidatesResponse)
def list_snap_candidates(
    query: SnapCandidatesRequest,
    network: Annotated[RouteNetwork, Depends(get_network)],
) -> SnapCandidatesResponse:
    candidates = candidates_within_limit(
        network,
        query.latitude,
        query.longitude,
        query.max_walk_meters,
    )
    return SnapCandidatesResponse(
        minimum_distance_meters=round(candidates[0].distance_km * 1_000),
        count=len(candidates),
        candidates=[
            SnapCandidateResponse(
                station=candidate.station,
                distance_meters=round(candidate.distance_km * 1_000),
            )
            for candidate in candidates
        ],
    )
