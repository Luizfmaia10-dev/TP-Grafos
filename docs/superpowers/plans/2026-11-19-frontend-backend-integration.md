# Frontend-Backend Integration Implementation Plan

> Documento histórico: registra decisões e instruções da época, não tarefas abertas atuais. O progresso vigente está em [docs/PLAN.md](../../PLAN.md); contratos atuais em [API.md](../../API.md).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the existing route planner to the FastAPI station and route endpoints, render the returned multimodal itinerary, and draw its steps on the SVG map with observable loading and failure states.

**Architecture:** A single API adapter converts FastAPI snake_case DTOs into small camelCase view models. Independent request controllers own cancellation and stale-response protection for autocomplete and route searches. Existing selection, timeline, and map modules consume normalized data and the application entry point only coordinates them.

**Tech Stack:** Vanilla JavaScript ES modules, native Fetch API, Node test runner, HTML, Tailwind CSS 4, FastAPI static serving.

**Spec:** `docs/superpowers/specs/2026-11-19-frontend-backend-integration-design.md`

## Global Constraints

- Use native browser APIs and add no dependency.
- Keep the backend API and graph domain unchanged.
- Send departure time as `HH:MM`, without seconds.
- Use English for identifiers and Portuguese for user-facing copy.
- Preserve cancellation and reject stale autocomplete and route results.
- Apply strict TDD: write and run each failing test before production code.
- Keep BUS `#e11d48`, SUBWAY `#209dd7`, WALK `#888888`, and temporary emphasis `#ecad0a`.
- Do not restore the removed expand-map or road-mapping animation.

---

### Task 1: Fetch API Adapter and Route Error State

**Files:**
- Create: `frontend/js/api-service.js`
- Create: `frontend/tests/api-service.test.js`
- Modify: `frontend/js/route-request.js`
- Modify: `frontend/tests/route-request.test.js`

**Interfaces:**
- Produces: `createApi(fetchImpl)` returning `{ listStations(query, options), searchRoute(query, options) }`.
- Produces: `ApiError` with public `kind` and `status` properties.
- Produces: normalized stations with `stationId`, `name`, `label`, `mapName`, `shortName`, `latitude`, and `longitude`.
- Produces: normalized route states consumed by Tasks 3–5.
- Changes: `createRouteRequest` error state from `{ status: "error" }` to `{ status: "error", error }`.

- [ ] **Step 1: Write failing station adapter tests**

Create a complete station fixture and assert the observable HTTP contract and normalized result:

```js
test("station search encodes the query and normalizes FastAPI stations", async () => {
  const calls = [];
  const api = createApi(async (url, options) => {
    calls.push({ url, options });
    return new Response(JSON.stringify([{
      station_id: "001", name: "Estação Central",
      latitude: -19.9, longitude: -43.9,
    }]), { status: 200, headers: { "content-type": "application/json" } });
  });
  const signal = new AbortController().signal;

  const stations = await api.listStations("São Gabriel", { signal, limit: 7 });

  assert.equal(calls[0].url, "/stations?query=S%C3%A3o+Gabriel&limit=7");
  assert.equal(calls[0].options.signal, signal);
  assert.deepEqual(stations[0], {
    stationId: "001", name: "Estação Central", label: "Estação Central",
    mapName: "Estação Central", shortName: "Estação Central",
    latitude: -19.9, longitude: -43.9,
  });
});
```

- [ ] **Step 2: Run the station adapter test and verify RED**

Run: `node --test tests/api-service.test.js`

Expected: FAIL because `../js/api-service.js` does not exist.

- [ ] **Step 3: Write failing route and HTTP error tests**

Add one found response containing BUS, SUBWAY, and WALK steps. Assert the exact POST method, headers, body, signal, normalized `steps`, and unchanged `instructions`. Add table cases asserting that 404, 422, 503, and 500 reject with kinds `unknown-station`, `invalid`, `unavailable`, and `http` respectively.

```js
assert.deepEqual(JSON.parse(calls[0].options.body), {
  origin_id: "001", destination_id: "004", departure_time: "25:05",
});
assert.deepEqual(result.steps.map(step => step.vehicleType), ["BUS", "SUBWAY", "WALK"]);
await assert.rejects(
  () => failingApi.searchRoute(query),
  error => error instanceof ApiError && error.kind === "unavailable" && error.status === 503,
);
```

- [ ] **Step 4: Implement the minimal API boundary**

Implement `ApiError`, `mapStation`, `mapStep`, response parsing, and the factory. Keep the error mapping explicit:

```js
const ERROR_KINDS = new Map([[404, "unknown-station"], [422, "invalid"], [503, "unavailable"]]);

export class ApiError extends Error {
  constructor(kind, status, message) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
  }
}

export function createApi(fetchImpl = globalThis.fetch) {
  return {
    async listStations(query, { signal, limit = 20 } = {}) {
      const parameters = new URLSearchParams({ query, limit: String(limit) });
      const response = await fetchImpl(`/stations?${parameters}`, { signal });
      const payload = await readJson(response);
      return payload.map(mapStation);
    },
    async searchRoute(query, { signal } = {}) {
      const response = await fetchImpl("/routes/search", {
        method: "POST", signal,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          origin_id: query.originId,
          destination_id: query.destinationId,
          departure_time: query.departureTime,
        }),
      });
      return mapRouteResponse(await readJson(response), query);
    },
  };
}

const api = createApi();
export const listStations = api.listStations;
export const searchRoute = api.searchRoute;
```

For `status: "found"`, flatten the normalized `route` into the result state and preserve `query`. For `status: "no-route"`, return its service date, endpoints, and query without creating route fields.

- [ ] **Step 5: Run adapter tests and verify GREEN**

Run: `node --test tests/api-service.test.js`

Expected: all adapter tests PASS.

- [ ] **Step 6: Preserve the route request error in TDD order**

First add this assertion to `route-request.test.js` and run it to observe `{ status: "error" }`:

```js
const failure = new ApiError("unavailable", 503, "unavailable");
const request = createRouteRequest(async () => { throw failure; }, state => states.push(state));
await request.submit({});
assert.equal(request.state.error, failure);
```

Then change only the catch branch to publish `{ status: "error", error }`. Run:

`node --test tests/route-request.test.js tests/api-service.test.js`

Expected: PASS.

- [ ] **Step 7: Commit Task 1**

```powershell
git add frontend/js/api-service.js frontend/js/route-request.js frontend/tests/api-service.test.js frontend/tests/route-request.test.js
git commit -m "feat(integração): conecta o cliente aos endpoints REST"
```

---

### Task 2: Cancelable Station Autocomplete State

**Files:**
- Create: `frontend/js/station-request.js`
- Create: `frontend/tests/station-request.test.js`
- Modify: `frontend/js/selection.js`
- Modify: `frontend/tests/selection.test.js`

**Interfaces:**
- Consumes: `listStations(query, { signal })` from Task 1.
- Produces: `createStationRequest(search, onChange)` with `state`, `submit(query)`, and `cancel()`.
- Produces states: `{ status: "idle" }`, `{ status: "loading", query }`, `{ status: "ready", query, stations }`, `{ status: "empty", query, stations: [] }`, and `{ status: "error", query, error }`.
- Changes: `validateSelection(selection)` trusts only confirmed non-null IDs and matching non-empty stored labels; it no longer imports a static catalog.

- [ ] **Step 1: Write and run failing autocomplete lifecycle tests**

Cover loading-to-ready, empty results, error, abort, and a late older response. The late-response test must use deferred promises and prove only the most recent station list is published:

```js
test("an older station response cannot replace a newer query", async () => {
  const pending = new Map();
  const request = createStationRequest((query) => new Promise(resolve => pending.set(query, resolve)), () => {});
  const oldCall = request.submit("cent");
  const newCall = request.submit("central");
  pending.get("central")([{ stationId: "2", label: "Central" }]);
  await newCall;
  pending.get("cent")([{ stationId: "1", label: "Old" }]);
  await oldCall;
  assert.deepEqual(request.state.stations.map(station => station.stationId), ["2"]);
});
```

Run: `node --test tests/station-request.test.js`

Expected: FAIL because the module does not exist.

- [ ] **Step 2: Implement and verify the request controller**

Use one AbortController and a monotonically increasing version. Unlike route submission, every `submit` aborts the prior station request. Ignore abort rejections and results whose version is no longer current. `cancel()` publishes idle.

Run: `node --test tests/station-request.test.js`

Expected: PASS.

- [ ] **Step 3: Write failing selection tests without the demonstration catalog**

Replace imports of `DEMO_STATIONS` with literal confirmed stations. Add a test proving that selecting an API station validates even when its ID was never present in the old sample, and retain tests for edited labels, unknown/unselected IDs, equal endpoints, and minute-only time.

```js
const remoteStation = { stationId: "remote-42", label: "Terminal Norte" };
let selection = selectStation(createSelection(), "origin", remoteStation);
selection = selectStation(selection, "destination", { stationId: "remote-43", label: "Terminal Sul" });
assert.equal(validateSelection(selection).query.originId, "remote-42");
```

Run: `node --test tests/selection.test.js`

Expected: FAIL while `selection.js` still resolves IDs through `DEMO_STATIONS`.

- [ ] **Step 4: Remove the static catalog dependency and verify GREEN**

Delete the `DEMO_STATIONS` import and `searchStations`. Validate a selected station with the pair of fields already controlled by selection:

```js
const origin = selection.originId && selection.originText.trim()
  ? { stationId: selection.originId }
  : null;
```

Keep equal-station and `HH:MM` validation unchanged. Run:

`node --test tests/selection.test.js tests/station-request.test.js`

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```powershell
git add frontend/js/station-request.js frontend/js/selection.js frontend/tests/station-request.test.js frontend/tests/selection.test.js
git commit -m "feat(autocomplete): consulta estações sem aceitar respostas antigas"
```

---

### Task 3: Multimodal Itinerary Timeline

**Files:**
- Modify: `frontend/js/route-view.js`
- Create: `frontend/tests/route-view.test.js`
- Modify: `frontend/index.html`
- Modify: `frontend/styles/app.css`
- Modify: `frontend/assets/app.css` through the CSS build

**Interfaces:**
- Consumes: normalized found result from Task 1.
- Produces: `buildTimelineEntries(result)` for deterministic presentation testing.
- Produces: `renderRoute(result)` that fills summary and `#itinerary-steps`.
- Produces entries with `kind` equal to `origin`, `wait`, `bus`, `subway`, `walk`, or `destination`.

- [ ] **Step 1: Write and run failing timeline model tests**

Use a literal result with one waiting BUS step, one SUBWAY step, and one WALK step. The instructions array must include four exact backend strings. Assert entries are ordered as origin, wait, bus, subway, walk, destination; assert each movement entry carries the matching API instruction, time, route ID, and stations.

```js
assert.deepEqual(
  buildTimelineEntries(result).map(entry => entry.kind),
  ["origin", "wait", "bus", "subway", "walk", "destination"],
);
assert.equal(entries[2].description, result.instructions[1]);
assert.equal(entries[4].routeId, "walk");
```

Run: `node --test tests/route-view.test.js`

Expected: FAIL because `buildTimelineEntries` is not exported.

- [ ] **Step 2: Implement timeline entry construction and verify GREEN**

Consume instructions with an index. A positive `waitingSeconds` consumes one wait instruction before the movement instruction. Always add explicit origin and destination entries around the steps. Map modes through this literal presentation table:

```js
const MODALS = {
  BUS: { kind: "bus", label: "Ônibus" },
  SUBWAY: { kind: "subway", label: "Metrô" },
  WALK: { kind: "walk", label: "Caminhada" },
};
```

Run: `node --test tests/route-view.test.js`

Expected: PASS.

- [ ] **Step 3: Write a failing DOM rendering test**

Use a minimal document fake whose nodes retain `textContent`, `className`, `dataset`, `style`, children, and `replaceChildren`. Assert:

- total, exact total, arrival, wait, travel, and distance are filled from the result;
- `#vehicle-duration` says `em deslocamento`, not `no ônibus`;
- the list contains modal-specific classes and the exact API instructions.

Run: `node --test tests/route-view.test.js`

Expected: FAIL against the demonstration-only renderer.

- [ ] **Step 4: Adapt the renderer and modal styles**

Render every timeline entry with `itinerary-step--${kind}`. Keep complete timestamps in `title`/accessible exact text and display a timestamp without only the final `:SS`. Update the itinerary note to describe real GTFS routing. Add CSS variables/classes so BUS is red, SUBWAY blue, WALK gray/dashed, wait yellow, and endpoint markers retain A/B styling.

Run:

```powershell
npm run build
node --test tests/route-view.test.js
```

Expected: build and tests PASS.

- [ ] **Step 5: Commit Task 3**

```powershell
git add frontend/js/route-view.js frontend/tests/route-view.test.js frontend/index.html frontend/styles/app.css frontend/assets/app.css
git commit -m "feat(itinerário): renderiza instruções por modal na timeline"
```

---

### Task 4: Dynamic Multimodal SVG Route

**Files:**
- Modify: `frontend/js/map.js`
- Modify: `frontend/tests/map.test.js`
- Modify: `frontend/index.html`
- Modify: `frontend/styles/app.css`
- Modify: `frontend/assets/app.css` through the CSS build

**Interfaces:**
- Consumes: normalized stations and normalized found route from Task 1.
- Produces: `buildRouteSegments(steps, layout)` returning `{ mode, points }` for each API step.
- Changes: `createStationMap(container, onSelect)` returns `{ setStations(stations), update(selection, activeField, result) }`.
- Produces: route SVG children with `route-glow route-segment--<mode>` and `route-line route-segment--<mode>` classes.

- [ ] **Step 1: Write and run failing projection/segment tests**

Keep the existing coordinate projection tests but replace imported demo fixtures with literal stations. Add BUS, SUBWAY, and WALK steps and assert exact projected point strings and modal order for desktop and mobile.

```js
const steps = [
  {
    vehicleType: "BUS",
    origin: { longitude: -44.045, latitude: -19.803 },
    destination: { longitude: -43.861, latitude: -19.803 },
  },
  {
    vehicleType: "SUBWAY",
    origin: { longitude: -43.861, latitude: -19.803 },
    destination: { longitude: -43.861, latitude: -19.968 },
  },
  {
    vehicleType: "WALK",
    origin: { longitude: -43.861, latitude: -19.968 },
    destination: { longitude: -44.045, latitude: -19.968 },
  },
];
assert.deepEqual(buildRouteSegments(steps, "desktop"), [
  { mode: "bus", points: "0,0 960,0" },
  { mode: "subway", points: "960,0 960,780" },
  { mode: "walk", points: "960,780 0,780" },
]);
```

Derive the expected numeric coordinates by hand from `MAP_LAYOUTS`, not by calling `projectStation` in the assertion.

Run: `node --test tests/map.test.js`

Expected: FAIL because `buildRouteSegments` is absent.

- [ ] **Step 2: Implement pure segment construction and verify GREEN**

Map each step independently so transfers retain their own modal. Reject no data only by returning `[]`; do not invent coordinates. Use lowercase CSS mode names.

Run: `node --test tests/map.test.js`

Expected: PASS.

- [ ] **Step 3: Write failing SVG and station-registry tests**

Use small element fakes supporting `ownerDocument.createElementNS`, attributes, `replaceChildren`, and events. Assert that:

- `setStations` replaces old station controls and preserves one control per station ID;
- `update(selection, activeField, result)` creates two polylines per step;
- route reset removes all SVG children;
- the legend contains only the modes present.

Run: `node --test tests/map.test.js`

Expected: FAIL against the fixed demonstration map.

- [ ] **Step 4: Render dynamic stations and SVG segments**

Build station controls inside `setStations`, deduplicate by `stationId`, and keep the existing click, selection, coordinate, label-collision, and ResizeObserver behavior. Create SVG nodes safely:

```js
const line = route.ownerDocument.createElementNS("http://www.w3.org/2000/svg", "polyline");
line.setAttribute("points", segment.points);
line.setAttribute("class", `route-line route-segment--${segment.mode}`);
```

Remove the fixed route polylines, arrow, and line-50 pill from `index.html`. Add modal segment CSS and a dashed WALK rule. Run:

```powershell
npm run build
node --test tests/map.test.js
```

Expected: build and tests PASS.

- [ ] **Step 5: Commit Task 4**

```powershell
git add frontend/js/map.js frontend/tests/map.test.js frontend/index.html frontend/styles/app.css frontend/assets/app.css
git commit -m "feat(mapa): desenha cada trecho da rota conforme o modal"
```

---

### Task 5: Application Wiring, Loading States, and Acceptance

**Files:**
- Modify: `frontend/js/app.js`
- Modify: `frontend/index.html`
- Modify: `frontend/styles/app.css`
- Modify: `frontend/assets/app.css` through the CSS build
- Delete: `frontend/js/demo-data.js`
- Delete: `frontend/js/demo-service.js`
- Delete: `frontend/tests/demo-service.test.js`
- Modify: `docs/FRONTEND_INTEGRATION.md`
- Modify: `docs/PLAN.md`

**Interfaces:**
- Consumes: `listStations`, `searchRoute`, `createStationRequest`, normalized selection, timeline renderer, and dynamic map from Tasks 1–4.
- Produces: the complete browser flow with no demonstration service in the active module graph.

- [ ] **Step 1: Write a failing API-flow integration test**

Add `frontend/tests/integration-flow.test.js` that uses `createApi`, `createStationRequest`, `createRouteRequest`, selection functions, `buildTimelineEntries`, and `buildRouteSegments` together with one in-memory Fetch boundary. Prove the user-visible data flow:

```js
await stationRequest.submit("central");
selection = selectStation(selection, "origin", stationRequest.state.stations[0]);
selection = selectStation(selection, "destination", destination);
await routeRequest.submit(validateSelection(selection).query);
assert.equal(routeRequest.state.status, "found");
assert.deepEqual(buildTimelineEntries(routeRequest.state).map(item => item.kind), ["origin", "bus", "destination"]);
assert.equal(buildRouteSegments(routeRequest.state.steps, "desktop")[0].mode, "bus");
```

Run: `node --test tests/integration-flow.test.js`

Expected: FAIL until the final module interfaces and normalized flow agree.

- [ ] **Step 2: Wire asynchronous station search into `app.js`**

Replace demo imports with:

```js
import { listStations, searchRoute, ApiError } from "./api-service.js";
import { createStationRequest } from "./station-request.js";
```

Maintain `knownStations = new Map()` as the union of search results, selected stations, and route-step stations. Create one station request controller per field. `openOptions(field)` submits the current input text; its change callback renders loading, ready, empty, or error into that field without opening another field. Cancel on clear, close, and selection. Set `aria-busy` on the station picker while loading.

- [ ] **Step 3: Wire route search and result/error rendering**

Construct `createRouteRequest(searchRoute, renderRequest)`. On found results, add every step endpoint to `knownStations`, call `renderRoute`, and pass the result to the map. On idle, no-route, or error, clear the previous timeline and route. Map errors by observed type/status:

```js
const ERROR_MESSAGES = {
  "unknown-station": ["Parada não encontrada", "Escolha novamente a origem e o destino."],
  invalid: ["Dados inválidos", "Confira as paradas e o horário de saída."],
  unavailable: ["Rede indisponível", "O servidor ainda não carregou a rede de transporte."],
};
```

Use a separate generic network message when `state.error` is not `ApiError`. Keep `aria-busy`, disable the submit button during loading, and announce cancellation-safe status copy.

- [ ] **Step 4: Remove demonstration UI and show autocomplete loading**

Delete the fixed line-50 trigger, sample scope, fixed platform/district wording, and example-only copy. Replace the empty option text with real-network wording. Add a small `.station-loading` state in the existing dropdown area, using text plus `aria-live`; do not add an animated map component. Update `createStationMap` call and call `map.setStations(Array.from(knownStations.values()))` whenever the union changes.

- [ ] **Step 5: Verify the integration test turns GREEN and run all frontend checks**

Run:

```powershell
npm run build
npm test
npm run check:server
```

Expected: CSS build succeeds; every frontend unit/integration test and static-server check passes.

- [ ] **Step 6: Verify the unchanged backend contract**

From `backend/`, run:

```powershell
$env:PYTHONPATH = Join-Path $env:TEMP 'tp-grafos-review-psutil'
C:\Users\ferna\TP-Grafos\.venv\Scripts\python.exe -m pytest -q
```

Expected: all backend tests pass with no new failure.

- [ ] **Step 7: Perform browser smoke verification**

Start FastAPI with a synthetic or configured GTFS network, open the served frontend, and verify:

1. Typing loads real station suggestions and exposes a loading state.
2. Selecting two stations and `HH:MM` submits one POST.
3. A found route shows timeline and colored SVG segments.
4. Editing cancels/clears the visible result.
5. No-route and unavailable-network states show their distinct messages.
6. Desktop and narrow viewport remain usable with no console error.

- [ ] **Step 8: Update documentation and progress only after acceptance passes**

Rewrite `docs/FRONTEND_INTEGRATION.md` to describe the live API flow and remove the historical demonstration contract. In `docs/PLAN.md`, change only these five checkboxes from `[ ]` to `[x]`:

- visual loading indicator in Part 7;
- Fetch events in Part 8;
- itinerary timeline in Part 8;
- SVG route in Part 8;
- extreme frontend cases in Part 8.

- [ ] **Step 9: Commit Task 5**

```powershell
git add frontend docs/FRONTEND_INTEGRATION.md docs/PLAN.md
git commit -m "feat(frontend): integra a busca real de trajetos"
```

---

## Final Verification

- [ ] Run `npm run build`, `npm test`, and `npm run check:server` from `frontend/`.
- [ ] Run the full `pytest -q` suite from `backend/`.
- [ ] Run `git diff --check` and confirm `git status --short` is empty.
- [ ] Review commits for task isolation and verify no frontend production module imports `demo-data.js` or `demo-service.js`.
- [ ] Request a whole-branch code review against the design specification before integration.
