"""Calendar-driven loading must only create edges for active service days."""

import csv
from datetime import date

import pytest

from app.data_loader import DataLoader
from app.domain import Station


CALENDAR_HEADER = (
    'service_id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
    'saturday', 'sunday', 'start_date', 'end_date',
)
DATES_HEADER = ('service_id', 'date', 'exception_type')
WEEKDAY = ('weekday', '1', '1', '1', '1', '1', '0', '0', '20260101', '20261231')
WEEKEND = ('weekend', '0', '0', '0', '0', '0', '1', '1', '20260101', '20261231')


@pytest.fixture
def calendar_feed(tmp_path):
    tables = {
        'stops.txt': [('stop_id','stop_name','stop_lat','stop_lon'),
                      ('A','Central','-19.9167','-43.9345'),
                      ('B','Terminal','-19.9100','-43.9400')],
        'routes.txt': [('route_id','route_type'), ('r','3')],
        'trips.txt': [('route_id','service_id','trip_id'),
                      ('r','weekday','weekday-trip'), ('r','weekend','weekend-trip')],
        'stop_times.txt': [('trip_id','arrival_time','departure_time','stop_id','stop_sequence'),
                           ('weekday-trip','08:00:00','08:00:00','A','1'),
                           ('weekday-trip','08:10:00','08:10:00','B','2'),
                           ('weekend-trip','09:00:00','09:00:00','A','1'),
                           ('weekend-trip','09:10:00','09:10:00','B','2')],
        'calendar.txt': [CALENDAR_HEADER, WEEKDAY, WEEKEND],
    }

    def write(**overrides):
        for name, rows in (tables | overrides).items():
            path = tmp_path / name
            if rows is None:
                path.unlink(missing_ok=True)
                continue
            with path.open('w', encoding='utf-8', newline='') as source:
                csv.writer(source).writerows(rows)
        return tmp_path

    return write


@pytest.mark.parametrize('day,expected', [
    (date(2026,11,17), ['weekday']),
    (date(2026,11,21), ['weekend']),
    (date(2026,11,22), ['weekend']),
    (date(2026,1,1), ['weekday']),
    (date(2026,12,31), ['weekday']),
    (date(2027,1,1), []),
    (date(2025,12,31), []),
])
def test_loads_only_services_active_on_date(calendar_feed, day, expected):
    loader = DataLoader(calendar_feed(), service_date=day)
    graph = loader.build_graph()
    connections = graph.get_neighbors(Station('A','',0,0))
    assert len(connections) == len(expected)
    if expected:
        assert connections[0].departure_time == (480 if expected == ['weekday'] else 540)
    report = loader.report.to_dict()
    assert report['active_service_ids'] == expected
    assert report['service_date'] == day.isoformat()
    assert report['connections'] == len(expected)
    assert report['files']['stop_times.txt']['accepted'] == 2 * len(expected)


def test_exceptions_add_and_remove_service_after_weekly_rules(calendar_feed):
    path = calendar_feed(**{'calendar_dates.txt': [DATES_HEADER,
        ('weekday','20261117','2'), ('weekend','20261117','1'),
        ('weekday','20261118','2')]})
    loader = DataLoader(path, service_date=date(2026,11,17))
    graph = loader.build_graph()
    connection, = graph.get_neighbors(Station('A','',0,0))
    assert connection.departure_time == 540
    assert loader.report.to_dict()['active_service_ids'] == ['weekend']
    assert loader.report.reasons['inactive_service'] == 2


def test_exception_can_add_service_outside_regular_period(calendar_feed):
    path = calendar_feed(**{'calendar_dates.txt': [DATES_HEADER, ('weekend','20270101','1')]})
    loader = DataLoader(path, service_date=date(2027,1,1))
    loader.build_graph()
    assert loader.report.loaded_trips == 1
    assert loader.report.to_dict()['active_service_ids'] == ['weekend']


def test_calendar_dates_can_define_all_services_without_calendar(calendar_feed):
    path = calendar_feed(**{'calendar.txt': None,
        'calendar_dates.txt': [DATES_HEADER, ('weekday','20261117','1')]})
    loader = DataLoader(path, service_date=date(2026,11,17))
    loader.build_graph()
    assert loader.report.loaded_trips == 1
    assert loader.report.to_dict()['active_service_ids'] == ['weekday']


def test_calendar_services_absent_from_trips_do_not_reject_valid_date(calendar_feed):
    extra = ('unused', *WEEKDAY[1:])
    loader = DataLoader(calendar_feed(**{'calendar.txt': [CALENDAR_HEADER, WEEKDAY, extra]}),
                        service_date=date(2026,11,17))
    loader.build_graph()
    assert loader.report.to_dict()['active_service_ids'] == ['weekday']


def test_missing_calendars_fail_instead_of_guessing(calendar_feed):
    path = calendar_feed(**{'calendar.txt': None})
    with pytest.raises(FileNotFoundError, match='calendar'):
        DataLoader(path, service_date=date(2026,11,17)).build_graph()


def test_manual_service_selection_and_date_are_mutually_exclusive(calendar_feed):
    with pytest.raises(ValueError, match='mutually exclusive'):
        DataLoader(calendar_feed(), active_service_ids={'weekday'}, service_date=date(2026,11,17))


@pytest.mark.parametrize('row', [
    ('weekday','2',*WEEKDAY[2:]),
    (*WEEKDAY[:-2],'20260230','20261231'),
    (*WEEKDAY[:-2],'2026011','20261231'),
    (*WEEKDAY[:-2],'20261231','20260101'),
    ('',*WEEKDAY[1:]),
])
def test_invalid_calendar_rows_fail_clearly(calendar_feed, row):
    path = calendar_feed(**{'calendar.txt': [CALENDAR_HEADER, row]})
    with pytest.raises(ValueError, match='calendar.txt'):
        DataLoader(path, service_date=date(2026,11,17)).build_graph()


@pytest.mark.parametrize('rows', [
    [DATES_HEADER, ('weekday','20261117','3')],
    [DATES_HEADER, ('weekday','20260230','1')],
    [DATES_HEADER, ('','20261117','1')],
    [DATES_HEADER, ('weekday','20261117','1'), ('weekday','20261117','2')],
])
def test_invalid_exceptions_fail_clearly(calendar_feed, rows):
    path = calendar_feed(**{'calendar_dates.txt': rows})
    with pytest.raises(ValueError, match='calendar_dates.txt'):
        DataLoader(path, service_date=date(2026,11,17)).build_graph()


def test_duplicate_calendar_service_fails_clearly(calendar_feed):
    path = calendar_feed(**{'calendar.txt': [CALENDAR_HEADER, WEEKDAY, WEEKDAY]})
    with pytest.raises(ValueError, match='calendar.txt'):
        DataLoader(path, service_date=date(2026,11,17)).build_graph()


@pytest.mark.parametrize('rows', [[('service_id',), ('weekday',)],
                                 [CALENDAR_HEADER, ('weekday','1')]])
def test_invalid_calendar_structure_fails_clearly(calendar_feed, rows):
    path = calendar_feed(**{'calendar.txt': rows})
    with pytest.raises(ValueError, match='calendar.txt'):
        DataLoader(path, service_date=date(2026,11,17)).build_graph()


def test_rebuild_for_another_date_replaces_service_selection(calendar_feed):
    loader = DataLoader(calendar_feed(), service_date=date(2026,11,17))
    first = loader.build_graph()
    loader.service_date = date(2026,11,21)
    second = loader.build_graph()
    assert first.get_neighbors(Station('A','',0,0))[0].departure_time == 480
    assert second.get_neighbors(Station('A','',0,0))[0].departure_time == 540
    assert loader.report.to_dict()['active_service_ids'] == ['weekend']
    assert loader.report.to_dict()['service_date'] == '2026-11-21'
