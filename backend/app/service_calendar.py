"""Resolve GTFS service IDs from weekly calendars and date exceptions."""

from collections.abc import Iterator
from csv import DictReader
from datetime import date
from pathlib import Path

WEEKDAYS = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')


def _rows(path: Path, required: tuple[str, ...]) -> Iterator[tuple[int, dict[str, str]]]:
    """Fail on malformed calendars rather than silently guessing availability."""
    with path.open(encoding='utf-8-sig', newline='') as source:
        reader = DictReader(source)
        headers = reader.fieldnames or []
        if not set(required) <= set(headers) or len(set(headers)) != len(headers):
            raise ValueError(f'{path.name}: invalid header')
        for row in reader:
            if None in row or None in row.values():
                raise ValueError(f'{path.name}:{reader.line_num}: incorrect number of fields')
            cleaned = {key: value.strip() for key, value in row.items()}
            if any(not cleaned[key] for key in required):
                raise ValueError(f'{path.name}:{reader.line_num}: missing required value')
            yield reader.line_num, cleaned


def _date(value: str) -> date:
    """Parse the GTFS YYYYMMDD date representation without permissive padding."""
    if len(value) != 8 or not value.isascii() or not value.isdigit():
        raise ValueError('expected YYYYMMDD')
    return date.fromisoformat(value)


def get_active_service_ids(data_directory: Path, service_date: date) -> set[str]:
    """Apply inclusive validity ranges, weekday flags, then explicit exceptions."""
    calendar = data_directory / 'calendar.txt'
    exceptions = data_directory / 'calendar_dates.txt'
    if not calendar.is_file() and not exceptions.is_file():
        raise FileNotFoundError('service_date requires calendar.txt or calendar_dates.txt')
    active = set()
    if calendar.is_file():
        seen_services = set()
        required = ('service_id', *WEEKDAYS, 'start_date', 'end_date')
        for line, row in _rows(calendar, required):
            try:
                start, end = _date(row['start_date']), _date(row['end_date'])
                if start > end:
                    raise ValueError('start_date is after end_date')
                if any(row[day] not in ('0', '1') for day in WEEKDAYS):
                    raise ValueError('weekday flags must be 0 or 1')
                if row['service_id'] in seen_services:
                    raise ValueError('duplicate service_id')
            except ValueError as error:
                raise ValueError(f'calendar.txt:{line}: {error}') from None
            seen_services.add(row['service_id'])
            if start <= service_date <= end and row[WEEKDAYS[service_date.weekday()]] == '1':
                active.add(row['service_id'])
    if exceptions.is_file():
        seen_exceptions = set()
        for line, row in _rows(exceptions, ('service_id', 'date', 'exception_type')):
            try:
                exception_date = _date(row['date'])
                if row['exception_type'] not in ('1', '2'):
                    raise ValueError('exception_type must be 1 or 2')
                key = row['service_id'], exception_date
                if key in seen_exceptions:
                    raise ValueError('duplicate service_id/date')
            except ValueError as error:
                raise ValueError(f'calendar_dates.txt:{line}: {error}') from None
            seen_exceptions.add(key)
            if exception_date == service_date:
                if row['exception_type'] == '1':
                    active.add(row['service_id'])
                else:
                    active.discard(row['service_id'])
    return active
