"""Static event expansion preserving scheduled earliest-arrival queries."""
from bisect import bisect_left
from itertools import pairwise
from time import perf_counter_ns

import networkx as nx

from app.domain import VehicleType


class NetworkXAdapter:
    """Dijkstra reference for scheduled connections, with query-local endpoints."""

    __slots__ = ('graph', 'events', 'last_timings')

    def __init__(self, transport_graph):
        self.graph = nx.DiGraph()
        times = {station.station_id: set() for station in transport_graph.iter_stations()}
        for station in transport_graph.iter_stations():
            for connection in transport_graph.get_neighbors(station):
                if connection.vehicle_type is VehicleType.WALK:
                    raise ValueError('WALK is outside the scheduled benchmark scope')
                departure = connection.departure_time
                arrival = departure + connection.travel_time
                if connection.travel_time < 0:
                    raise ValueError('Negative travel duration')
                times[station.station_id].add(departure)
                times[connection.destination.station_id].add(arrival)
                self.graph.add_edge(
                    (station.station_id, departure),
                    (connection.destination.station_id, arrival),
                    weight=connection.travel_time, leg=(station, connection),
                )
        self.events = {key: sorted(values) for key, values in times.items()}
        for key, events in self.events.items():
            self.graph.add_nodes_from((key, time) for time in events)
            for start, end in pairwise(events):
                # An existing trip between these same events has identical cost.
                if not self.graph.has_edge((key, start), (key, end)):
                    self.graph.add_edge((key, start), (key, end), weight=end - start)
        self.last_timings = {}

    def calculate_route(self, origin, destination, departure_time):
        start = perf_counter_ns()
        source, target = object(), object()
        self.graph.add_nodes_from((source, target))
        try:
            if origin == destination:
                self.graph.add_edge(source, target, weight=0)
            else:
                events = self.events[origin.station_id]
                index = bisect_left(events, departure_time)
                if index < len(events):
                    event = events[index]
                    self.graph.add_edge(source, (origin.station_id, event),
                                        weight=event - departure_time)
                for event in self.events[destination.station_id]:
                    self.graph.add_edge((destination.station_id, event), target, weight=0)
            prepared = perf_counter_ns()
            try:
                _, nodes = nx.single_source_dijkstra(self.graph, source, target)
                path = [self.graph.edges[left, right]['leg']
                        for left, right in pairwise(nodes)
                        if 'leg' in self.graph.edges[left, right]]
            except nx.NetworkXNoPath:
                path = None
            searched = perf_counter_ns()
        finally:
            self.graph.remove_nodes_from((source, target))
        cleaned = perf_counter_ns()
        self.last_timings = {
            'query_prepare_ns': prepared - start,
            'search_ns': searched - prepared,
            'cleanup_ns': cleaned - searched,
            'query_total_ns': cleaned - start,
        }
        return path
