import assert from "node:assert/strict";
import test from "node:test";
import { DEMO_STATIONS } from "../js/demo-data.js";
import {
  createSelection,
  editStation,
  normalizeDepartureTime,
  searchStations,
  selectStation,
  validateSelection,
} from "../js/selection.js";

const [pampulha, rio, parana] = DEMO_STATIONS;

function readySelection() {
  let state = selectStation(createSelection(), "origin", pampulha);
  return selectStation(state, "destination", parana);
}

test("a new query requires both selected station IDs", () => {
  const result = validateSelection(createSelection());
  assert.equal(result.query, null);
  assert.ok(result.errors.origin);
  assert.ok(result.errors.destination);
  assert.equal(result.errors.departureTime, undefined);
});

test("choosing a station stores its ID and display label", () => {
  const original = createSelection();
  const state = selectStation(original, "origin", pampulha);
  assert.equal(state.originId, pampulha.stationId);
  assert.equal(state.originText, pampulha.label);
  assert.equal(original.originId, null);
});

test("typing the exact station name still requires selecting a result", () => {
  const state = editStation(createSelection(), "origin", pampulha.label);
  assert.equal(state.originId, null);
  assert.ok(validateSelection(state).errors.origin);
});

test("editing a selected name clears its old ID and preserves the other selection", () => {
  const original = readySelection();
  const state = editStation(original, "origin", "Rio de Janeiro");
  assert.equal(state.originId, null);
  assert.equal(state.originText, "Rio de Janeiro");
  assert.equal(state.destinationId, parana.stationId);
  assert.equal(original.originId, pampulha.stationId);
  assert.equal(validateSelection(state).query, null);
});

test("clearing and selecting again replaces the ID consistently", () => {
  const cleared = editStation(readySelection(), "origin", "");
  assert.equal(cleared.originId, null);
  assert.equal(cleared.originText, "");
  const selected = selectStation(cleared, "origin", rio);
  assert.equal(selected.originId, rio.stationId);
  assert.equal(selected.originText, rio.label);
  assert.ok(validateSelection(selected).query);
});

test("matching IDs are rejected for origin and destination", () => {
  const state = selectStation(readySelection(), "destination", pampulha);
  const result = validateSelection(state);
  assert.equal(result.query, null);
  assert.ok(result.errors.destination);
});

test("a stale ID cannot validate a different label", () => {
  const state = { ...readySelection(), originText: rio.label };
  assert.ok(validateSelection(state).errors.origin);
});

test("unknown station IDs are rejected", () => {
  const state = { ...readySelection(), originId: "not-in-the-sample" };
  assert.equal(validateSelection(state).query, null);
});

test("a valid query contains selected IDs and normalized seconds", () => {
  const result = validateSelection(readySelection());
  assert.deepEqual(result.errors, {});
  assert.deepEqual(result.query, {
    originId: pampulha.stationId,
    destinationId: parana.stationId,
    departureTime: "07:45:00",
  });
});

test("extended hours and seconds are preserved in the query", () => {
  const state = { ...readySelection(), departureTime: "25:15:30" };
  assert.equal(validateSelection(state).query.departureTime, "25:15:30");
});

test("an invalid time blocks an otherwise valid query", () => {
  const state = { ...readySelection(), departureTime: "08:60" };
  assert.equal(validateSelection(state).query, null);
  assert.ok(validateSelection(state).errors.departureTime);
});

for (const [input, expected] of [
  ["00:00", "00:00:00"], ["07:45", "07:45:00"], ["08:30:45", "08:30:45"],
  ["23:59:59", "23:59:59"], ["24:00", "24:00:00"], ["25:00", "25:00:00"],
  ["48:00:01", "48:00:01"], ["100:15:30", "100:15:30"],
]) {
  test(`normalizes ${input} without wrapping service-day hours`, () => {
    assert.equal(normalizeDepartureTime(input), expected);
  });
}

for (const input of [
  "", "7:45", "07:5", "08:60", "08:30:60", "-01:00", "+08:00", "08:30:00.5",
  " 08:30", "08:30 ", "08:30\n", "08:30:00\n", "０８:30", "08:30:00:00",
]) {
  test(`rejects malformed time ${JSON.stringify(input)}`, () => {
    assert.equal(normalizeDepartureTime(input), null);
  });
}

test("a blank station search returns the available sample stops", () => {
  assert.deepEqual(searchStations(""), DEMO_STATIONS);
});

test("station searches ignore accents and letter case", () => {
  assert.deepEqual(searchStations("  ESTACAO PAMPULHA  "), [pampulha]);
  assert.deepEqual(searchStations("avenida paraná"), [parana]);
});

test("station searches include platform and abbreviated display names", () => {
  assert.deepEqual(searchStations("G4"), [pampulha]);
  assert.deepEqual(searchStations("Av. Parana"), [parana]);
});

test("a shared station term can return several options", () => {
  assert.deepEqual(searchStations("Estação"), [pampulha, rio]);
});

test("a station outside the sample returns no options", () => {
  assert.deepEqual(searchStations("Estação São Gabriel"), []);
});
