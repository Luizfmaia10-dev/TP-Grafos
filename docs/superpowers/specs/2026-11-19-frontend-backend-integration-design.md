# Frontend-Backend Integration Design

## Scope

Connect the existing Vanilla JavaScript interface to the existing FastAPI contracts. The frontend must request stations for autocomplete, submit a route search, render the returned itinerary in the sidebar, draw every route step on the SVG map according to its vehicle type, and expose loading and failure states. The graph engine, API payloads, time picker, theme switch, and removed map animation remain unchanged.

## Constraints

- Use the native Fetch API and existing browser primitives; add no dependency.
- Keep API field-name conversion at one frontend boundary so the view code remains readable.
- Send departure time as `HH:MM`, without seconds, including service-day hours above 23.
- Preserve request cancellation and prevent stale autocomplete or route responses from replacing newer state.
- Keep function and variable names in English and user-facing copy in Portuguese.
- Preserve the current visual language and modal colors from `AGENTS.md`.
- Apply TDD to every behavior change.
- Do not change the backend contracts unless a failing integration test proves that they cannot satisfy this scope.

## API boundary

Create `frontend/js/api-service.js` as the only module that knows the HTTP field names.

- `listStations(query, { signal, limit = 20 } = {})` calls `GET /stations` with `query` and `limit` encoded through `URLSearchParams`.
- `searchRoute(query, { signal } = {})` calls `POST /routes/search` with JSON keys `origin_id`, `destination_id`, and `departure_time`.
- Successful station DTOs are normalized to `{ stationId, name, label, mapName, shortName, latitude, longitude }`. Labels use the real station name and never invent platform, district, or commercial line metadata.
- A found route is normalized to the existing request-state style, with `{ status: "found", serviceDate, origin, destination, query, arrivalTime, totalSeconds, waitingSeconds, travelSeconds, distanceKm, steps, instructions }`.
- A no-route response remains `{ status: "no-route", serviceDate, origin, destination, query }`.
- Non-success HTTP responses throw `ApiError` with `kind` equal to `invalid`, `unknown-station`, `unavailable`, or `http`. Fetch/JSON failures remain ordinary errors and are presented as network failures.

The adapter validates only the minimum response shape consumed by the interface. FastAPI remains responsible for full schema validation.

## Autocomplete and selection

Replace the in-memory demonstration search with requests to `GET /stations`. A small `createStationRequest(search, onChange)` controller owns one autocomplete request at a time:

- a new query aborts the previous query;
- only the latest response can publish results;
- it publishes `loading`, `ready`, `empty`, or `error`;
- clearing or closing a field cancels its request.

The station list displays the real name and station ID. While loading, the list area exposes a progress message and `aria-busy`. Empty and failure messages are distinct. Selecting a result stores its ID and label; editing the label invalidates the stored ID. Selection validation no longer imports a hard-coded catalog because a station ID can only be set by an API result or a map marker created from one.

The SVG map maintains the union of currently returned stations, selected endpoints, and stations in the current route. This preserves click-to-select without loading the entire GTFS catalog into the DOM.

## Route request and failure states

Reuse `createRouteRequest` for submission, AbortController cancellation, repeated-submit protection, and stale-response protection. Preserve the caught error in the published error state so the view can distinguish:

- no route at the selected time: HTTP 200 `status: "no-route"`;
- identical endpoints or invalid input: client validation / HTTP 422;
- a stale or unknown station: HTTP 404;
- network not configured: HTTP 503;
- transport, malformed JSON, or other HTTP errors.

During a route request, the form uses `aria-busy`, the submit button is disabled, its spinner remains visible, and status copy announces the operation. Editing either station or the time cancels the request and clears the obsolete result.

## Itinerary timeline

Render the route from `route.steps` and use the backend-provided `instructions` in order. For each step:

- if `waitingSeconds` is positive, consume and render the waiting instruction;
- render the travel instruction with its `vehicleType`, route ID, departure time, arrival time, origin, and destination;
- use modal-specific classes for `BUS`, `SUBWAY`, and `WALK`;
- finish with an arrival marker at the response destination.

The summary shows total time, arrival, total waiting, total travel, and distance. It must not label all travel as bus. Times shown in compact positions drop only a trailing `:SS`; exact accessible text keeps the complete API timestamp.

## SVG route

Replace the single demonstration polyline with SVG elements generated from normalized route steps. Each step is a line segment between the real coordinates of its origin and destination, projected through the existing desktop/mobile map bounds.

- `BUS`: `#e11d48`, solid.
- `SUBWAY`: `#209dd7`, solid.
- `WALK`: `#888888`, dashed; endpoint emphasis can use `#ecad0a` where already supported.

Every segment receives a wider translucent glow plus the visible line. Rendering uses `createElementNS`; no HTML string interpolation is used. The legend lists only the modes present. Resizing recomputes projected points. A no-route, edit, or cancelled search removes the old route immediately.

## Active demonstration removal

The application entry point must stop importing and calling `demo-data.js` and `demo-service.js`. Demonstration-specific button copy, fixed line 50 metadata, and example-only messages are removed from the active UI. Obsolete demonstration modules and tests may be deleted once equivalent API and rendering coverage exists.

## Tests and acceptance

Frontend unit tests use Node's test runner and small DOM fakes already used by the project. Fetch is replaced only at the network boundary with complete response fixtures.

Acceptance requires:

1. Autocomplete calls `/stations`, shows loading, cancels stale requests, and stores a real station ID.
2. Submission calls `/routes/search` with the exact documented JSON and `HH:MM` time.
3. A multimodal response renders waiting and travel instructions in order and shows accurate totals.
4. The map creates correctly colored BUS, SUBWAY, and WALK segments from response coordinates.
5. No-route, identical endpoints, 404, 422, 503, network failure, edit, and cancellation leave no stale itinerary or route.
6. Frontend tests, backend tests, static-server checks, production CSS build, and browser smoke verification pass.
7. Only the corresponding checkboxes in `docs/PLAN.md` change from `[ ]` to `[x]` after all acceptance checks pass.
