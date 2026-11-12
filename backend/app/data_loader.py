"""Stream and sanitize GTFS CSV files into the in-memory transport graph."""

from collections import Counter
from collections.abc import Callable, Iterator
from csv import DictReader
from dataclasses import asdict, dataclass, field
from itertools import groupby, pairwise
from math import asin, cos, isfinite, radians, sin, sqrt
from pathlib import Path
from typing import TypeVar

from app.domain import Connection, Station, VehicleType
from app.graph import TransportGraph
from app.time_utils import TimeUtils


@dataclass(slots=True)
class FileStatistics:
    """Count input records; accepted plus rejected equals read after success."""

    read: int = 0
    accepted: int = 0
    rejected: int = 0


@dataclass(slots=True)
class LoadReport:
    """Keep exact counters and at most five examples per diagnostic code."""

    files: dict[str, FileStatistics] = field(default_factory=dict)
    reasons: Counter = field(default_factory=Counter)
    warnings: Counter = field(default_factory=Counter)
    examples: dict[str, list[dict]] = field(default_factory=dict)
    rejected_trips: dict[str, str] = field(default_factory=dict)
    loaded_trips: int = 0
    connections: int = 0

    def to_dict(self) -> dict:
        """Return a JSON-compatible snapshot without exposing mutable counters."""
        return {
            'files': {name: asdict(stats) for name, stats in self.files.items()},
            'reasons': dict(self.reasons),
            'warnings': dict(self.warnings),
            'examples': {code: [dict(item) for item in items]
                         for code, items in self.examples.items()},
            'rejected_trips': dict(self.rejected_trips),
            'loaded_trips': self.loaded_trips,
            'connections': self.connections,
        }


T = TypeVar('T')


class DataLoader:
    """Load contiguous trip blocks; quarantine invalid trips before insertion.

    Route types 1 and 3 are supported. Distances are Haversine estimates in km.
    Service calendars and pickup/drop-off restrictions are not applied.
    """

    __slots__ = ('data_directory', 'report', '_times', '_distances', '_durations')

    _REQUIRED = {
        'stops.txt': ('stop_id', 'stop_name', 'stop_lat', 'stop_lon'),
        'routes.txt': ('route_id', 'route_type'),
        'trips.txt': ('trip_id', 'route_id', 'service_id'),
        'stop_times.txt': ('trip_id', 'stop_id', 'arrival_time',
                           'departure_time', 'stop_sequence'),
    }

    def __init__(self, data_directory: str | Path) -> None:
        self.data_directory = Path(data_directory)
        self.report = LoadReport()
        self._times: dict[str, float] = {}
        self._distances: dict[tuple[Station, Station], float] = {}
        self._durations: dict[float, float] = {}

    def _read_rows(self, filename: str) -> Iterator[tuple[int, dict[str, str]]]:
        """Validate CSV structure and strip outer whitespace, preserving IDs."""
        stats = self.report.files.setdefault(filename, FileStatistics())
        with (self.data_directory / filename).open(
            encoding='utf-8-sig', newline=''
        ) as source:
            reader = DictReader(source)
            headers = reader.fieldnames or []
            missing = set(self._REQUIRED[filename]) - set(headers)
            if missing or len(headers) != len(set(headers)):
                raise ValueError(f'{filename}: invalid header; missing {sorted(missing)}')
            for row in reader:
                stats.read += 1
                line = reader.line_num
                if None in row or None in row.values():
                    raise ValueError(f'{filename}:{line}: incorrect number of fields')
                yield line, {key: value.strip() for key, value in row.items()}

    def _example(self, code: str, filename: str, line: int | None, record_id: str) -> None:
        examples = self.report.examples.setdefault(code, [])
        if len(examples) < 5:
            examples.append({'file': filename, 'line': line, 'id': record_id})

    def _reject(self, filename: str, line: int, record_id: str,
                reason: str, count: int = 1) -> None:
        self.report.files[filename].rejected += count
        self.report.reasons[reason] += count
        self._example(reason, filename, line, record_id)

    def _load_records(self, filename: str, id_field: str,
                      parse: Callable[[dict[str, str]], T]) -> dict[str, T]:
        """Deduplicate identical rows; exclude every row of a conflicting ID."""
        records: dict[str, T] = {}
        originals = {}
        blocked = set()
        for line, row in self._read_rows(filename):
            record_id = row[id_field]
            if record_id in blocked:
                self._reject(filename, line, record_id, 'conflicting_id')
                continue
            if record_id in originals:
                old_row, old_line = originals[record_id]
                if old_row == row:
                    self._reject(filename, line, record_id, 'duplicate_record')
                else:
                    del records[record_id]
                    del originals[record_id]
                    blocked.add(record_id)
                    self.report.files[filename].accepted -= 1
                    self._reject(filename, old_line, record_id, 'conflicting_id')
                    self._reject(filename, line, record_id, 'conflicting_id')
                continue
            try:
                if any(not row[key] for key in self._REQUIRED[filename]):
                    raise ValueError('missing_required_value')
                value = parse(row)
            except ValueError as error:
                self._reject(filename, line, record_id, str(error))
                continue
            originals[record_id] = row, line
            records[record_id] = value
            self.report.files[filename].accepted += 1
        return records

    @staticmethod
    def _parse_station(row: dict[str, str]) -> Station:
        try:
            latitude, longitude = float(row['stop_lat']), float(row['stop_lon'])
        except ValueError:
            raise ValueError('invalid_coordinate') from None
        if not (isfinite(latitude) and isfinite(longitude)
                and -90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError('invalid_coordinate')
        return Station(row['stop_id'], row['stop_name'], latitude, longitude)

    @staticmethod
    def _parse_route(row: dict[str, str]) -> VehicleType:
        vehicle_type = {'1': VehicleType.SUBWAY, '3': VehicleType.BUS}.get(row['route_type'])
        if vehicle_type is None:
            raise ValueError('unsupported_route_type')
        return vehicle_type

    def build_graph(self) -> TransportGraph:
        """Build a fresh graph and reset diagnostics on each invocation."""
        self.report = LoadReport()
        self._times.clear()
        self._distances.clear()
        self._durations.clear()
        stations = self._load_records('stops.txt', 'stop_id', self._parse_station)
        routes = self._load_records('routes.txt', 'route_id', self._parse_route)

        def parse_trip(row: dict[str, str]) -> str:
            if row['route_id'] not in routes:
                raise ValueError('unknown_route')
            return row['route_id']

        trips = self._load_records('trips.txt', 'trip_id', parse_trip)
        graph = TransportGraph()
        for station in stations.values():
            graph.add_station(station)
        seen_trips = set()
        for trip_id, records in groupby(
            self._read_rows('stop_times.txt'), key=lambda item: item[1]['trip_id']
        ):
            if trip_id in seen_trips:
                raise ValueError(f'stop_times.txt: trip {trip_id!r} must be contiguous')
            seen_trips.add(trip_id)
            rows = list(records)
            try:
                if trip_id not in trips:
                    raise ValueError('unknown_trip')
                connections = self._trip_connections(rows, stations)
            except ValueError as error:
                reason = str(error)
                self.report.rejected_trips[trip_id] = reason
                self._reject('stop_times.txt', rows[0][0], trip_id, reason, len(rows))
                continue
            route_id = trips[trip_id]
            for origin, destination, departure, duration, distance, line in connections:
                if duration > 0 and distance / (duration / 60) > 120:
                    self.report.warnings['suspicious_speed'] += 1
                    self._example('suspicious_speed', 'stop_times.txt', line, trip_id)
                graph.add_connection(origin, Connection(
                    route_id, destination, routes[route_id], duration, distance, departure
                ))
            self.report.files['stop_times.txt'].accepted += len(rows)
            self.report.connections += len(connections)
            self.report.loaded_trips += 1
        for trip_id in trips.keys() - seen_trips:
            self.report.rejected_trips[trip_id] = 'missing_stop_times'
            self.report.warnings['missing_stop_times'] += 1
            self._example('missing_stop_times', 'trips.txt', None, trip_id)
        self._times.clear()
        self._distances.clear()
        self._durations.clear()
        return graph

    def _parse_time(self, value: str) -> float:
        """Share repeated immutable schedule values during a single load."""
        if value not in self._times:
            self._times[value] = TimeUtils.time_to_minutes(value)
        return self._times[value]

    def _trip_connections(self, rows: list[tuple[int, dict[str, str]]],
                          stations: dict[str, Station]) -> list[tuple]:
        """Validate a complete trip before creating any graph edges."""
        if len(rows) < 2:
            raise ValueError('too_few_stops')
        times = []
        sequences = set()
        for line, row in rows:
            if any(not row[key] for key in self._REQUIRED['stop_times.txt']):
                raise ValueError('missing_required_value')
            if row['stop_id'] not in stations:
                raise ValueError('unknown_stop')
            if not row['stop_sequence'].isascii() or not row['stop_sequence'].isdigit():
                raise ValueError('invalid_sequence')
            sequence = int(row['stop_sequence'])
            if sequence in sequences:
                raise ValueError('duplicate_sequence')
            sequences.add(sequence)
            try:
                arrival = self._parse_time(row['arrival_time'])
                departure = self._parse_time(row['departure_time'])
            except ValueError:
                raise ValueError('invalid_time') from None
            if departure < arrival:
                raise ValueError('departure_before_arrival')
            times.append((sequence, stations[row['stop_id']], arrival, departure, line))
        times.sort(key=lambda item: item[0])
        connections = []
        for current, following in pairwise(times):
            _, origin, _, departure, _ = current
            _, destination, arrival, _, line = following
            duration = arrival - departure
            if duration < 0:
                raise ValueError('negative_travel_time')
            if duration == 0 and origin != destination:
                raise ValueError('zero_travel_time')
            pair = origin, destination
            if pair not in self._distances:
                self._distances[pair] = self._calculate_distance(origin, destination)
            distance = self._distances[pair]
            duration = self._durations.setdefault(duration, duration)
            connections.append((origin, destination, departure, duration, distance, line))
        return connections

    @staticmethod
    def _calculate_distance(origin: Station, destination: Station) -> float:
        """Return Haversine distance in kilometers using a 6371 km Earth radius."""
        origin_latitude = radians(origin.latitude)
        destination_latitude = radians(destination.latitude)
        latitude_delta = destination_latitude - origin_latitude
        longitude_delta = radians(destination.longitude - origin.longitude)
        haversine = (
            sin(latitude_delta / 2) ** 2
            + cos(origin_latitude) * cos(destination_latitude)
            * sin(longitude_delta / 2) ** 2
        )
        return 2 * 6371 * asin(sqrt(min(1.0, haversine)))
