"""Station catalog endpoint for autocomplete."""

from itertools import islice
from typing import Annotated
from unicodedata import combining, normalize

from fastapi import APIRouter, Depends, Query

from app.domain import Station
from app.network import RouteNetwork, get_network

router = APIRouter(tags=["stations"])


def normalize_search(value: str) -> str:
    """Match names and IDs regardless of case, accents or outer whitespace."""
    unaccented = "".join(char for char in normalize("NFD", value) if not combining(char))
    return unaccented.casefold().strip()


@router.get("/stations", response_model=list[Station])
def list_stations(
    network: Annotated[RouteNetwork, Depends(get_network)],
    query: str = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Station]:
    """Return up to limit matches in catalog order, preserving station IDs."""
    search = normalize_search(query)
    matches = (
        station
        for station in network.stations.values()
        if search in normalize_search(station.name)
        or search in normalize_search(station.station_id)
    )
    return list(islice(matches, limit))
