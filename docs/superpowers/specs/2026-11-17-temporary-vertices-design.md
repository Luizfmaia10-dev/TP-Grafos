# Temporary Vertices Design

## Scope

Add snap-to-network support without implementing the pending A* search. A map
click becomes a temporary origin or destination connected by walking to the
nearest real station within 0.8 km. The temporary topology is removed after the
caller leaves the routing scope, including when an exception occurs.

## Domain

`TemporaryVertex` subclasses `Station`, keeps the inherited identifier, name and
coordinates, and adds `marker_type` (`"origin"` or `"destination"`). It remains
immutable and uses slots.

## Graph

`TransportGraph.remove_temporary_vertex(vertex)` deletes the vertex, its outgoing
adjacency list and every incoming connection whose destination is the vertex. It
keeps existing neighbor lists ordered and has `O(V + E)` cleanup cost.

## Snap-to-network

`RouteSimulator.snap_to_network(latitude, longitude, marker_type)` is a context
manager. It scans `graph.iter_stations()` in `O(V)`, ignores existing temporary
vertices, and chooses the real station with minimum Haversine distance. Missing
stations, invalid coordinates, invalid marker types, or a nearest station beyond
0.8 km raise `ValueError` without changing the graph.

The temporary vertex receives a UUID-based identifier. Walking uses 5 km/h,
`VehicleType.WALK`, route id `temporary-walk`, and distance in kilometers.
Travel time is `distance / (5 / 60)` minutes. An origin marker creates
`temporary -> station`; a destination marker creates `station -> temporary`.
Walking is unscheduled, so its stored departure time is `0.0`; the future A*
must handle `WALK` as immediately available instead of applying timetable
binary search to it.

The context manager removes the temporary vertex in `finally`, ensuring cleanup
after normal completion or exceptions.

## Tests and documentation

TDD covers specialization and slots, nearest-real-station selection, walking
direction and weight, the 800 m limit, invalid input, and cleanup. Completion
marks only the four matching checkboxes in `docs/PLAN.md`.
