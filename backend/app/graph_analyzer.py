"""Structural analysis of the permanent transport network."""

from app.domain import Station, TemporaryVertex
from app.graph import TransportGraph


class GraphAnalyzer:
    """Analyze real stations independently of schedules and travel times."""

    __slots__ = ("_graph",)

    def __init__(self, graph: TransportGraph) -> None:
        self._graph = graph

    def find_articulation_points(self) -> set[Station]:
        """Find cuts in the simple undirected projection of real stations."""
        return {
            station for station, score in self.criticality_scores().items() if score > 0
        }

    def find_strongly_connected_components(self) -> list[set[Station]]:
        """Run iterative Tarjan on the directed graph of real stations."""
        discovery: dict[Station, int] = {}
        lowpt: dict[Station, int] = {}
        active: set[Station] = set()
        component_stack: list[Station] = []
        components: list[set[Station]] = []

        for root in self._graph.iter_stations():
            if isinstance(root, TemporaryVertex) or root in discovery:
                continue
            discovery[root] = lowpt[root] = len(discovery)
            active.add(root)
            component_stack.append(root)
            frames = [(root, iter(self._graph.get_neighbors(root)))]

            while frames:
                station, connections = frames[-1]
                connection = next(connections, None)
                if connection is not None:
                    neighbor = connection.destination
                    if isinstance(neighbor, TemporaryVertex):
                        continue
                    if neighbor not in discovery:
                        discovery[neighbor] = lowpt[neighbor] = len(discovery)
                        active.add(neighbor)
                        component_stack.append(neighbor)
                        frames.append((neighbor, iter(self._graph.get_neighbors(neighbor))))
                    elif neighbor in active:
                        lowpt[station] = min(lowpt[station], discovery[neighbor])
                    continue

                frames.pop()
                if frames:
                    parent = frames[-1][0]
                    lowpt[parent] = min(lowpt[parent], lowpt[station])
                if lowpt[station] == discovery[station]:
                    component = set()
                    while True:
                        member = component_stack.pop()
                        active.remove(member)
                        component.add(member)
                        if member == station:
                            break
                    components.append(component)

        return components

    def criticality_scores(self) -> dict[Station, int]:
        """Return max(0, components(G-v) - components(G)) for every real station."""
        return self._criticality_scores(self._undirected_adjacency())

    def get_critical_stations(self, top_n: int) -> list[Station]:
        """Rank positive scores by impact, simple degree, then station ID.

        Return fewer than top_n stations when fewer stations have positive impact.
        """
        if top_n < 0:
            raise ValueError("top_n must be nonnegative")
        if top_n == 0:
            return []
        adjacency = self._undirected_adjacency()
        scores = self._criticality_scores(adjacency)
        return sorted(
            (station for station, score in scores.items() if score > 0),
            key=lambda station: (-scores[station], -len(adjacency[station]), station.station_id),
        )[:top_n]

    def _undirected_adjacency(self) -> dict[Station, set[Station]]:
        adjacency: dict[Station, set[Station]] = {
            station: set()
            for station in self._graph.iter_stations()
            if not isinstance(station, TemporaryVertex)
        }
        for station in adjacency:
            for connection in self._graph.get_neighbors(station):
                neighbor = connection.destination
                if isinstance(neighbor, TemporaryVertex) or neighbor == station:
                    continue
                adjacency[station].add(neighbor)
                adjacency[neighbor].add(station)
        return adjacency

    @staticmethod
    def _criticality_scores(adjacency: dict[Station, set[Station]]) -> dict[Station, int]:
        discovery: dict[Station, int] = {}
        lowpt: dict[Station, int] = {}
        scores = dict.fromkeys(adjacency, 0)

        for root in adjacency:
            if root in discovery:
                continue
            discovery[root] = lowpt[root] = len(discovery)
            frames = [(root, iter(adjacency[root]))]
            while frames:
                station, neighbors = frames[-1]
                neighbor = next(neighbors, None)
                if neighbor is not None:
                    if neighbor not in discovery:
                        discovery[neighbor] = lowpt[neighbor] = len(discovery)
                        frames.append((neighbor, iter(adjacency[neighbor])))
                    elif len(frames) < 2 or neighbor != frames[-2][0]:
                        lowpt[station] = min(lowpt[station], discovery[neighbor])
                    continue

                frames.pop()
                if frames:
                    parent = frames[-1][0]
                    lowpt[parent] = min(lowpt[parent], lowpt[station])
                    if lowpt[station] >= discovery[parent]:
                        scores[parent] += 1
            # A root has no parent-side component after removal.
            scores[root] = max(0, scores[root] - 1)

        return scores
