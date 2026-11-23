"""Transport itineraries independent of HTTP and presentation frameworks."""

import json
from dataclasses import asdict, dataclass

from app.domain import Connection, Station, VehicleType
from app.time_utils import TimeUtils


@dataclass(frozen=True, slots=True)
class ItineraryStep:
    """A traversed connection with effective timestamps and costs."""

    origin: Station
    destination: Station
    route_id: str
    route_short_name: str
    vehicle_type: VehicleType
    departure_time: str
    arrival_time: str
    waiting_seconds: int
    travel_seconds: int
    distance_km: float


@dataclass(frozen=True, slots=True, init=False)
class Itinerary:
    """Snapshot of an ordered path; durations are seconds, distances kilometers.

    Input timestamps and connection durations use fractional service-day minutes.
    Absolute timestamps are rounded before subtracting to keep costs additive.
    Construction takes O(N) time and space for N connections.
    """

    origin: Station
    destination: Station
    departure_time: str
    arrival_time: str
    total_seconds: int
    waiting_seconds: int
    travel_seconds: int
    distance_km: float
    steps: tuple[ItineraryStep, ...]
    instructions: tuple[str, ...]

    def __init__(
        self, origin: Station, departure_time: float,
        path: list[tuple[Station, Connection]],
    ) -> None:
        start_time = TimeUtils.minutes_to_time(departure_time)
        current_time = departure_time
        current_station = origin
        steps = []
        instructions = []
        for station, connection in path:
            if station != current_station:
                raise ValueError("Path must contain contiguous connections from origin")
            departure = (current_time if connection.vehicle_type is VehicleType.WALK
                         else connection.departure_time)
            if departure < current_time or connection.travel_time < 0:
                raise ValueError("Path must have nonnegative waiting and travel times")
            arrival = departure + connection.travel_time
            departure_seconds = round(departure * 60)
            arrival_seconds = round(arrival * 60)
            step = ItineraryStep(
                station, connection.destination, connection.route_id,
                connection.route_short_name or "Linha não informada", connection.vehicle_type,
                TimeUtils.minutes_to_time(departure), TimeUtils.minutes_to_time(arrival),
                departure_seconds - round(current_time * 60),
                arrival_seconds - departure_seconds, connection.distance,
            )
            steps.append(step)
            if step.waiting_seconds > 0:
                instructions.append(f"Aguarde em {station.name} até {step.departure_time}.")
            if step.vehicle_type is VehicleType.WALK:
                instructions.append(
                    f"Caminhe de {station.name} até {step.destination.name} "
                    f"às {step.departure_time}; chegada às {step.arrival_time}."
                )
            else:
                mode = "ônibus" if step.vehicle_type is VehicleType.BUS else "metrô"
                instructions.append(
                    f"Pegue o {mode} {step.route_short_name} de {station.name} "
                    f"até {step.destination.name} às {step.departure_time}; "
                    f"chegada às {step.arrival_time}."
                )
            current_time = arrival
            current_station = connection.destination

        values = {
            "origin": origin, "destination": current_station,
            "departure_time": start_time,
            "arrival_time": TimeUtils.minutes_to_time(current_time),
            "total_seconds": round(current_time * 60) - round(departure_time * 60),
            "waiting_seconds": sum(step.waiting_seconds for step in steps),
            "travel_seconds": sum(step.travel_seconds for step in steps),
            "distance_km": sum(step.distance_km for step in steps),
            "steps": tuple(steps), "instructions": tuple(instructions),
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)

    def to_dict(self) -> dict:
        """Return an independent JSON-compatible representation in O(N)."""
        result = asdict(self)
        result["steps"] = [
            {**asdict(step), "vehicle_type": step.vehicle_type.value}
            for step in self.steps
        ]
        result["instructions"] = list(self.instructions)
        return result

    def to_json(self) -> str:
        """Serialize the itinerary, preserving non-ASCII station names."""
        return json.dumps(self.to_dict(), ensure_ascii=False, allow_nan=False)
