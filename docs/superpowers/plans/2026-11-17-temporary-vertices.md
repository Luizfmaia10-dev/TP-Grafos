# Temporary Vertices Implementation Plan

> Documento histórico: registra decisões e instruções da época, não tarefas abertas atuais. O progresso vigente está em [docs/PLAN.md](../../PLAN.md); contratos atuais em [API.md](../../API.md).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Snap arbitrary map coordinates to the nearest real station within 800 m, add directional walking topology, and always clean it after use.

**Architecture:** Add the immutable domain specialization first, then graph-owned removal, then a context-managed snap operation in `RouteSimulator`. Reuse the existing Haversine function and station iterator; add no dependency or spatial index.

**Tech Stack:** Python standard library, native adjacency lists, `pytest`.

**Spec:** `docs/superpowers/specs/2026-11-17-temporary-vertices-design.md`

## Global Constraints

- Use English for code names and internal documentation.
- Use `__slots__` on domain data classes.
- Do not add graph-processing libraries or visual dependencies.
- Keep the station search as a simple `O(V)` scan for the MVP.
- Write and observe each failing test before production code.

---

### Task 1: TemporaryVertex domain type

**Files:**
- Modify: `backend/app/domain.py`
- Test: `backend/tests/test_entities.py`

**Interfaces:**
- Produces: `TemporaryVertex(Station)` with `marker_type: str`.

- [x] Add a failing test that instantiates `TemporaryVertex`, verifies inherited fields, `marker_type`, station identity and absence of `__dict__`.
- [x] Run `python -m pytest tests/test_entities.py -q` and verify import failure.
- [x] Implement `@dataclass(frozen=True, eq=False, slots=True) class TemporaryVertex(Station)` with only `marker_type: str`.
- [x] Re-run the entity tests and verify they pass.

### Task 2: Temporary graph cleanup

**Files:**
- Modify: `backend/app/graph.py`
- Test: `backend/tests/test_graph.py`

**Interfaces:**
- Consumes: `TemporaryVertex`.
- Produces: `TransportGraph.remove_temporary_vertex(vertex: TemporaryVertex) -> None`.

- [x] Add a failing test with outgoing and incoming temporary connections; assert removal keeps all real vertices and real edges.
- [x] Run the targeted graph test and verify missing-method failure.
- [x] Implement deletion of the temporary key plus in-place filtering of incoming connections.
- [x] Re-run all graph tests and verify they pass.

### Task 3: Context-managed snap-to-network

**Files:**
- Modify: `backend/app/route_simulator.py`
- Test: `backend/tests/test_route_simulator.py`

**Interfaces:**
- Consumes: `TransportGraph.iter_stations`, `remove_temporary_vertex`, `haversine`, `Connection`, `TemporaryVertex`, `VehicleType`.
- Produces: `RouteSimulator.snap_to_network(latitude: float, longitude: float, marker_type: str) -> AbstractContextManager[TemporaryVertex]`.

- [x] Add failing tests for nearest real station, origin/destination edge direction, walking distance/time, exclusion of existing temporary vertices and cleanup after normal completion.
- [x] Run the targeted tests and verify the missing-method failure.
- [x] Implement the `O(V)` nearest-real-station scan, UUID identity, directional `WALK` connection and normal cleanup.
- [x] Add failing tests for invalid coordinates/marker, no real station within 0.8 km and cleanup after exceptions.
- [x] Implement validation, the 0.8 km boundary and `try/finally` cleanup.
- [x] Re-run all route simulator tests and verify they pass.

### Task 4: Progress and final verification

**Files:**
- Modify: `docs/PLAN.md`

**Interfaces:**
- Produces: four completed checkboxes for removal, specialization/snap, walking connection and automatic cleanup.

- [x] Change only the four applicable `[ ]` markers to `[x]` in `docs/PLAN.md`.
- [x] Run `python -m pytest --cov=app --cov-report=term-missing` from `backend/`.
- [x] Run `python -m compileall -q app tests` and `git diff --check`.
- [x] Review the final diff against the spec and confirm no A*, API or frontend work was added.
