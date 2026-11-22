import assert from "node:assert/strict";
import test from "node:test";
import {
  createSelection,
  editStation,
  normalizeDepartureTime,
  selectStation,
  validateSelection,
} from "../js/selection.js";

const pampulha = { stationId: "remote-42", label: "Terminal Norte" };
const rio = { stationId: "remote-43", label: "Terminal Sul" };
const parana = { stationId: "remote-44", label: "Terminal Leste" };

function readySelection() {
  let state = selectStation(createSelection(), "origin", pampulha);
  return selectStation(state, "destination", parana);
}

test("a query requires confirmed IDs and non-empty labels for both stations", () => {
  const result = validateSelection(createSelection());
  assert.equal(result.query, null);
  assert.ok(result.errors.origin);
  assert.ok(result.errors.destination);
  assert.equal(result.errors.departureTime, undefined);

  for (const field of ["origin", "destination"]) {
    for (const change of [{ [`${field}Id`]: null }, { [`${field}Text`]: " \t " }]) {
      const invalid = validateSelection({ ...readySelection(), ...change });
      assert.equal(invalid.query, null);
      assert.deepEqual(Object.keys(invalid.errors), [field]);
    }
  }
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
  assert.equal(result.errors.origin, undefined);
});

test("an API station outside the demonstration catalog validates after selection", () => {
  let state = selectStation(createSelection(), "origin", pampulha);
  state = selectStation(state, "destination", rio);
  assert.deepEqual(validateSelection(state).query, {
    originId: "remote-42", destinationId: "remote-43", departureTime: "07:45",
  });
});

test("a valid query contains selected IDs and a minute-only departure", () => {
  const result = validateSelection(readySelection());
  assert.deepEqual(result.errors, {});
  assert.deepEqual(result.query, {
    originId: pampulha.stationId,
    destinationId: parana.stationId,
    departureTime: "07:45",
  });
});

test("extended hours are preserved in the query", () => {
  const state = { ...readySelection(), departureTime: "25:15" };
  assert.equal(validateSelection(state).query.departureTime, "25:15");
});

test("an invalid time blocks an otherwise valid query", () => {
  const state = { ...readySelection(), departureTime: "08:60" };
  assert.equal(validateSelection(state).query, null);
  assert.ok(validateSelection(state).errors.departureTime);
});

for (const [input, expected] of [
  ["00:00", "00:00"], ["07:45", "07:45"], ["23:59", "23:59"],
  ["24:00", "24:00"], ["25:00", "25:00"], ["100:15", "100:15"],
]) {
  test(`normalizes ${input} without wrapping service-day hours`, () => {
    assert.equal(normalizeDepartureTime(input), expected);
  });
}

for (const input of [
  "", "7:45", "07:5", "08:60", "08:30:00", "08:30:60", "-01:00", "+08:00", "08:30:00.5",
  " 08:30", "08:30 ", "08:30\n", "08:30:00\n", "０８:30", "08:30:00:00",
]) {
  test(`rejects malformed time ${JSON.stringify(input)}`, () => {
    assert.equal(normalizeDepartureTime(input), null);
  });
}
