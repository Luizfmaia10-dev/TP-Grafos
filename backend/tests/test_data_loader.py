"""Contract tests for loading GTFS files into the transport graph."""

import pytest

from app.domain import Station, VehicleType
from app.graph import TransportGraph


def test_build_graph_connects_consecutive_stops_in_a_valid_trip(tmp_path):
    """Load A -> B -> C, including the scheduled stopover at B."""
    from app.data_loader import DataLoader

    files = {
        "stops.txt": (
            "stop_id,stop_name,stop_lat,stop_lon\n"
            "A,Central,-19.9167,-43.9345\n"
            "B,Lagoinha,-19.9100,-43.9400\n"
            "C,Terminal,-19.9000,-43.9500\n"
        ),
        "routes.txt": (
            "route_id,route_short_name,route_long_name,route_type\n"
            "route-1,101,Central to Terminal,3\n"
        ),
        "trips.txt": (
            "route_id,service_id,trip_id\n"
            "route-1,weekday,trip-1\n"
        ),
        "stop_times.txt": (
            "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
            "trip-1,08:00:00,08:00:00,A,1\n"
            "trip-1,08:10:30,08:12:00,B,2\n"
            "trip-1,08:20:00,08:20:00,C,3\n"
        ),
    }
    for filename, content in files.items():
        (tmp_path / filename).write_text(content, encoding="utf-8")

    graph = DataLoader(tmp_path).build_graph()

    assert isinstance(graph, TransportGraph)
    origin = Station("A", "Central", -19.9167, -43.9345)
    middle = Station("B", "Lagoinha", -19.9100, -43.9400)
    destination = Station("C", "Terminal", -19.9000, -43.9500)
    first_connections = graph.get_neighbors(origin)
    second_connections = graph.get_neighbors(middle)

    assert len(first_connections) == 1
    assert len(second_connections) == 1
    assert graph.get_neighbors(destination) == []

    first = first_connections[0]
    second = second_connections[0]
    assert first.destination == middle
    assert second.destination == destination
    assert first.destination.name == "Lagoinha"
    assert first.destination.latitude == pytest.approx(-19.9100)
    assert first.destination.longitude == pytest.approx(-43.9400)
    assert second.destination.name == "Terminal"
    assert second.destination.latitude == pytest.approx(-19.9000)
    assert second.destination.longitude == pytest.approx(-43.9500)
    assert first.route_id == second.route_id == "route-1"
    assert first.vehicle_type is second.vehicle_type is VehicleType.BUS
    assert first.departure_time == pytest.approx(480.0)
    assert first.travel_time == pytest.approx(10.5)
    assert second.departure_time == pytest.approx(492.0)
    assert second.travel_time == pytest.approx(8.0)
    assert first.distance == pytest.approx(0.941098, abs=0.000001)
    assert second.distance == pytest.approx(1.526284, abs=0.000001)


def test_build_graph_skips_stop_with_non_numeric_latitude(tmp_path):
    """Reject a malformed coordinate and continue loading subsequent stops."""
    from app.data_loader import DataLoader

    files = {
        "stops.txt": (
            "stop_id,stop_name,stop_lat,stop_lon\n"
            "invalid,Invalid,abc,-43.9400\n"
            "A,Central,-19.9167,-43.9345\n"
        ),
        "routes.txt": "route_id,route_type\n",
        "trips.txt": "route_id,service_id,trip_id\n",
        "stop_times.txt": (
            "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        ),
    }
    for filename, content in files.items():
        (tmp_path / filename).write_text(content, encoding="utf-8")

    graph = DataLoader(tmp_path).build_graph()

    valid_station = Station("A", "Central", -19.9167, -43.9345)
    invalid_station = Station("invalid", "Invalid", 0.0, -43.9400)
    assert graph.get_neighbors(valid_station) == []
    with pytest.raises(KeyError):
        graph.get_neighbors(invalid_station)


@pytest.fixture
def gtfs_feed(tmp_path):
    """Write a small valid feed that individual tests can override."""
    import csv

    defaults = {
        'stops': [('stop_id', 'stop_name', 'stop_lat', 'stop_lon'),
                  ('A', 'Central', '-19.9167', '-43.9345'),
                  ('B', 'Terminal', '-19.9100', '-43.9400')],
        'routes': [('route_id', 'route_type'), ('r', '3')],
        'trips': [('route_id', 'service_id', 'trip_id'), ('r', 'weekday', 't')],
        'stop_times': [('trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'),
                       ('t', '08:00:00', '08:00:00', 'A', '1'),
                       ('t', '08:10:00', '08:10:00', 'B', '2')],
    }

    def write(**overrides):
        for name, rows in (defaults | overrides).items():
            with (tmp_path / (name + '.txt')).open('w', encoding='utf-8', newline='') as f:
                csv.writer(f).writerows(rows)
        from app.data_loader import DataLoader
        return DataLoader(tmp_path)

    return write


@pytest.mark.parametrize('latitude,longitude', [
    ('91', '0'), ('-91', '0'), ('0', '181'), ('0', '-181'),
    ('nan', '0'), ('0', 'inf'), ('-inf', '0'), ('', '0'), ('0', ''), ('0', 'abc'),
])
def test_invalid_coordinates_reject_dependent_trip(gtfs_feed, latitude, longitude):
    loader = gtfs_feed(stops=[('stop_id', 'stop_name', 'stop_lat', 'stop_lon'),
                             ('A', 'Bad', latitude, longitude),
                             ('B', 'Terminal', '-19.9100', '-43.9400')])
    graph = loader.build_graph()
    assert graph.get_neighbors(Station('B', '', 0, 0)) == []
    with pytest.raises(KeyError):
        graph.get_neighbors(Station('A', '', 0, 0))
    assert loader.report.files['stops.txt'].rejected == 1
    assert loader.report.rejected_trips['t'] == 'unknown_stop'
    assert loader.report.connections == 0


@pytest.mark.parametrize('station_id,name', [('', 'Central'), ('A', ''), ('A', '   ')])
def test_required_station_fields(gtfs_feed, station_id, name):
    loader = gtfs_feed(stops=[('stop_id', 'stop_name', 'stop_lat', 'stop_lon'),
                             (station_id, name, '-19.9167', '-43.9345'),
                             ('B', 'Terminal', '-19.9100', '-43.9400')])
    loader.build_graph()
    assert loader.report.files['stops.txt'].rejected == 1
    assert loader.report.connections == 0


def test_identical_duplicate_is_ignored_and_conflict_rejects_both(gtfs_feed):
    header = ('stop_id', 'stop_name', 'stop_lat', 'stop_lon')
    a = ('A', 'Central', '-19.9167', '-43.9345')
    b = ('B', 'Terminal', '-19.9100', '-43.9400')
    loader = gtfs_feed(stops=[header, a, a, b])
    loader.build_graph()
    assert loader.report.connections == 1
    assert loader.report.reasons['duplicate_record'] == 1
    loader = gtfs_feed(stops=[header, a, ('A', 'Conflict', '-19.9167', '-43.9345'), a, b])
    graph = loader.build_graph()
    assert loader.report.files['stops.txt'].rejected == 3
    assert loader.report.reasons['conflicting_id'] == 3
    with pytest.raises(KeyError):
        graph.get_neighbors(Station('A', '', 0, 0))


@pytest.mark.parametrize('table,rows,reason', [
    ('routes', [('route_id', 'route_type'), ('r', '99')], 'unknown_trip'),
    ('routes', [('route_id', 'route_type'), ('r', '')], 'unknown_trip'),
    ('trips', [('route_id', 'service_id', 'trip_id'), ('missing', 'weekday', 't')], 'unknown_trip'),
    ('trips', [('route_id', 'service_id', 'trip_id'), ('r', '', 't')], 'unknown_trip'),
])
def test_invalid_route_or_trip_rejects_times(gtfs_feed, table, rows, reason):
    loader = gtfs_feed(**{table: rows})
    loader.build_graph()
    assert loader.report.connections == 0
    assert loader.report.files[table + '.txt'].rejected == 1
    assert loader.report.rejected_trips['t'] == reason


@pytest.mark.parametrize('rows,reason', [
    ([('t','','08:00:00','A','1'), ('t','08:10:00','08:10:00','B','2')], 'missing_required_value'),
    ([('t','bad','08:00:00','A','1'), ('t','08:10:00','08:10:00','B','2')], 'invalid_time'),
    ([('t','08:01:00','08:00:00','A','1'), ('t','08:10:00','08:10:00','B','2')], 'departure_before_arrival'),
    ([('t','08:00:00','08:00:00','A','1'), ('t','07:59:00','07:59:00','B','2')], 'negative_travel_time'),
    ([('t','08:00:00','08:00:00','A','1'), ('t','08:10:00','08:10:00','B','1')], 'duplicate_sequence'),
    ([('t','08:00:00','08:00:00','A','-1'), ('t','08:10:00','08:10:00','B','2')], 'invalid_sequence'),
    ([('t','08:00:00','08:00:00','A','x'), ('t','08:10:00','08:10:00','B','2')], 'invalid_sequence'),
    ([('t','08:00:00','08:00:00','A','1')], 'too_few_stops'),
    ([('t','08:00:00','08:00:00','A','1'), ('t','08:10:00','08:10:00','missing','2')], 'unknown_stop'),
])
def test_invalid_trip_is_rejected_atomically(gtfs_feed, rows, reason):
    header = ('trip_id','arrival_time','departure_time','stop_id','stop_sequence')
    loader = gtfs_feed(stop_times=[header, *rows])
    graph = loader.build_graph()
    assert graph.get_neighbors(Station('A', '', 0, 0)) == []
    assert loader.report.connections == 0
    assert loader.report.rejected_trips['t'] == reason
    assert loader.report.files['stop_times.txt'].rejected == len(rows)


def test_sorts_sequence_preserves_spaces_and_extended_hours(gtfs_feed):
    loader = gtfs_feed(
        trips=[('route_id','service_id','trip_id'), (' r ',' weekday ','trip   one')],
        stop_times=[('trip_id','arrival_time','departure_time','stop_id','stop_sequence'),
                    ('trip   one','25:10:30','25:10:30',' B ','20'),
                    ('trip   one','25:00:00','25:00:00',' A ','10')])
    graph = loader.build_graph()
    connection, = graph.get_neighbors(Station('A', '', 0, 0))
    assert connection.departure_time == 1500
    assert connection.travel_time == 10.5
    assert loader.report.loaded_trips == 1


def test_quarantines_zero_time_and_warns_on_high_speed(gtfs_feed):
    header = ('trip_id','arrival_time','departure_time','stop_id','stop_sequence')
    loader = gtfs_feed(stop_times=[header, ('t','08:00:00','08:00:00','A','1'),
                                  ('t','08:00:00','08:00:00','B','2')])
    loader.build_graph()
    assert loader.report.rejected_trips['t'] == 'zero_travel_time'
    assert loader.report.connections == 0
    loader = gtfs_feed(stop_times=[header, ('t','08:00:00','08:00:00','A','1'),
                                  ('t','08:00:01','08:00:01','B','2')])
    loader.build_graph()
    assert loader.report.connections == 1
    assert loader.report.warnings['suspicious_speed'] == 1


def test_rejecting_one_trip_does_not_join_or_remove_other_trips(gtfs_feed):
    loader = gtfs_feed(
        trips=[('route_id','service_id','trip_id'), ('r','weekday','bad'), ('r','weekday','good')],
        stop_times=[('trip_id','arrival_time','departure_time','stop_id','stop_sequence'),
                    ('bad','08:00:00','08:00:00','A','1'),
                    ('bad','08:00:00','08:00:00','B','2'),
                    ('good','09:00:00','09:00:00','A','1'),
                    ('good','09:10:00','09:10:00','B','2')])
    graph = loader.build_graph()
    connection, = graph.get_neighbors(Station('A', '', 0, 0))
    assert connection.departure_time == 540
    assert loader.report.loaded_trips == 1
    assert loader.report.files['stop_times.txt'].accepted == 2
    assert loader.report.files['stop_times.txt'].rejected == 2


def test_report_is_serializable_balanced_and_reset_on_rebuild(gtfs_feed):
    import json
    loader = gtfs_feed()
    loader.build_graph()
    first = loader.report.to_dict()
    assert first['connections'] == 1
    assert first['loaded_trips'] == 1
    json.dumps(first)
    for stats in first['files'].values():
        assert stats['read'] == stats['accepted'] + stats['rejected']
    loader.build_graph()
    assert loader.report.to_dict() == first


@pytest.mark.parametrize('filename', ['stops', 'routes', 'trips', 'stop_times'])
def test_missing_required_column_fails_clearly(gtfs_feed, filename):
    loader = gtfs_feed(**{filename: [('unrelated',), ('value',)]})
    with pytest.raises(ValueError, match=filename + '.txt'):
        loader.build_graph()


def test_missing_file_fails_clearly(gtfs_feed):
    loader = gtfs_feed()
    (loader.data_directory / 'routes.txt').unlink()
    with pytest.raises(FileNotFoundError):
        loader.build_graph()


def test_fragmented_trip_fails_instead_of_returning_partial_route(gtfs_feed):
    loader = gtfs_feed(
        trips=[('route_id','service_id','trip_id'), ('r','weekday','t'), ('r','weekday','other')],
        stop_times=[('trip_id','arrival_time','departure_time','stop_id','stop_sequence'),
                    ('t','08:00:00','08:00:00','A','1'),
                    ('other','09:00:00','09:00:00','A','1'),
                    ('other','09:10:00','09:10:00','B','2'),
                    ('t','08:10:00','08:10:00','B','2')])
    with pytest.raises(ValueError, match='contiguous'):
        loader.build_graph()


@pytest.mark.parametrize('latitude,longitude', [('90','180'), ('-90','-180')])
def test_geographic_boundaries_are_valid(gtfs_feed, latitude, longitude):
    loader = gtfs_feed(stops=[('stop_id','stop_name','stop_lat','stop_lon'),
                             ('A','Same name',latitude,longitude),
                             ('B','Same name','-19.9100','-43.9400')])
    loader.build_graph()
    assert loader.report.files['stops.txt'].accepted == 2
    assert loader.report.connections == 1


def test_subway_and_optional_empty_fields_are_supported(gtfs_feed):
    loader = gtfs_feed(routes=[('route_id','route_type','route_desc'), ('r','1','')])
    graph = loader.build_graph()
    connection, = graph.get_neighbors(Station('A','',0,0))
    assert connection.vehicle_type is VehicleType.SUBWAY


@pytest.mark.parametrize('table,header,first,conflict', [
    ('routes', ('route_id','route_type'), ('r','3'), ('r','1')),
    ('trips', ('route_id','service_id','trip_id'), ('r','weekday','t'), ('r','weekend','t')),
])
def test_conflicting_route_or_trip_does_not_leave_stale_index(
    gtfs_feed, table, header, first, conflict
):
    loader = gtfs_feed(**{table: [header,first,conflict]})
    loader.build_graph()
    assert loader.report.connections == 0
    stats = loader.report.files[table + '.txt']
    assert stats.read == stats.rejected == 2
    assert stats.accepted == 0


def test_zero_time_at_end_does_not_leave_first_connection(gtfs_feed):
    loader = gtfs_feed(
        stops=[('stop_id','stop_name','stop_lat','stop_lon'),
               ('A','Central','-19.9167','-43.9345'),
               ('B','Middle','-19.9100','-43.9400'),
               ('C','Terminal','-19.9000','-43.9500')],
        stop_times=[('trip_id','arrival_time','departure_time','stop_id','stop_sequence'),
                    ('t','08:00:00','08:00:00','A','1'),
                    ('t','08:10:00','08:10:00','B','2'),
                    ('t','08:10:00','08:10:00','C','3')])
    graph = loader.build_graph()
    assert graph.get_neighbors(Station('A','',0,0)) == []
    assert graph.get_neighbors(Station('B','',0,0)) == []
    assert loader.report.reasons['zero_travel_time'] == 3


def test_trip_without_stop_times_is_reported(gtfs_feed):
    loader = gtfs_feed(stop_times=[('trip_id','arrival_time','departure_time','stop_id','stop_sequence')])
    loader.build_graph()
    assert loader.report.rejected_trips == {'t': 'missing_stop_times'}
    assert loader.report.warnings['missing_stop_times'] == 1
    assert loader.report.loaded_trips == 0


def test_report_limits_examples_without_losing_counts(gtfs_feed):
    rows = [('stop_id','stop_name','stop_lat','stop_lon')]
    rows.extend((str(i),'Bad','nan','0') for i in range(10))
    loader = gtfs_feed(stops=rows)
    loader.build_graph()
    assert loader.report.reasons['invalid_coordinate'] == 10
    assert len(loader.report.examples['invalid_coordinate']) == 5
    snapshot = loader.report.to_dict()
    snapshot['examples']['invalid_coordinate'][0]['id'] = 'changed'
    assert loader.report.examples['invalid_coordinate'][0]['id'] == '0'
    for stats in loader.report.files.values():
        assert stats.read == stats.accepted + stats.rejected


def test_incorrect_csv_width_fails_clearly(gtfs_feed):
    loader = gtfs_feed(stops=[('stop_id','stop_name','stop_lat','stop_lon'), ('A','Central','0')])
    with pytest.raises(ValueError, match='stops.txt:2: incorrect number of fields'):
        loader.build_graph()


def test_utf8_bom_and_quoted_station_name(gtfs_feed):
    loader = gtfs_feed(stops=[('stop_id','stop_name','stop_lat','stop_lon'),
                             (' A ',' Praça, Central ','-19.9167','-43.9345'),
                             ('B','Terminal','-19.9100','-43.9400')])
    path = loader.data_directory / 'stops.txt'
    path.write_bytes(b'\xef\xbb\xbf' + path.read_bytes())
    graph = loader.build_graph()
    connection, = graph.get_neighbors(Station('A','',0,0))
    assert connection.destination.station_id == 'B'
    assert loader.report.files['stops.txt'].accepted == 2


def test_rebuild_recalculates_distances_after_coordinates_change(gtfs_feed):
    loader = gtfs_feed()
    first_graph = loader.build_graph()
    first_connection, = first_graph.get_neighbors(Station('A', '', 0, 0))
    path = loader.data_directory / 'stops.txt'
    path.write_text(path.read_text().replace('-19.9100', '-19.9000'), encoding='utf-8')
    second_graph = loader.build_graph()
    second_connection, = second_graph.get_neighbors(Station('A', '', 0, 0))
    assert second_connection.distance > first_connection.distance
    assert first_connection.travel_time == second_connection.travel_time == 10


def test_repeated_station_pair_keeps_each_trips_own_schedule(gtfs_feed):
    loader = gtfs_feed(
        trips=[('route_id','service_id','trip_id'), ('r','weekday','first'), ('r','weekday','second')],
        stop_times=[('trip_id','arrival_time','departure_time','stop_id','stop_sequence'),
                    ('first','08:00:00','08:00:00','A','1'),
                    ('first','08:10:00','08:10:00','B','2'),
                    ('second','09:00:00','09:00:00','A','1'),
                    ('second','09:20:00','09:20:00','B','2')])
    graph = loader.build_graph()
    first, second = graph.get_neighbors(Station('A','',0,0))
    assert (first.departure_time, first.travel_time) == (480, 10)
    assert (second.departure_time, second.travel_time) == (540, 20)
    assert first.distance == second.distance
    assert loader.report.loaded_trips == 2
    assert loader.report.connections == 2
