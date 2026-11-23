import assert from "node:assert/strict";
import test from "node:test";
import {
  createAddressSelection,
  selectOriginStation,
  setAddress,
  setSnapCandidates,
  setSnapUnavailable,
  setWalkLimit,
  validateAddressSelection,
} from "../js/address-selection.js";

const originAddress = {
  label: "Rua da Origem, 10, Belo Horizonte - MG",
  latitude: -19.9,
  longitude: -43.9,
};
const destinationAddress = {
  label: "Rua do Destino, 20, Belo Horizonte - MG",
  latitude: -19.91,
  longitude: -43.91,
};
const candidates = [
  { station: { stationId: "001", label: "Parada 1" }, distanceMeters: 240 },
  { station: { stationId: "002", label: "Parada 2" }, distanceMeters: 510 },
];

test("address selection starts with independent 800 metre limits", () => {
  const state = createAddressSelection();

  assert.equal(state.origin.maxWalkMeters, 800);
  assert.equal(state.destination.maxWalkMeters, 800);
  assert.equal(state.origin.address, null);
  assert.equal(state.destination.address, null);
  assert.equal(state.departureTime, "07:45");
});

test("an address change clears stale candidates and selected origin station", () => {
  let state = setAddress(createAddressSelection(), "origin", originAddress);
  state = setSnapCandidates(state, "origin", {
    candidates,
    minimumDistanceMeters: 240,
  });
  state = selectOriginStation(state, "002");

  state = setAddress(state, "origin", { ...originAddress, label: "Outra rua" });

  assert.deepEqual(state.origin.candidates, []);
  assert.equal(state.origin.stationId, null);
  assert.equal(state.origin.minimumDistanceMeters, null);
});

test("origin candidates recommend the nearest station but allow another valid one", () => {
  let state = setAddress(createAddressSelection(), "origin", originAddress);
  state = setSnapCandidates(state, "origin", {
    candidates,
    minimumDistanceMeters: 240,
  });

  assert.equal(state.origin.stationId, "001");
  assert.equal(selectOriginStation(state, "002").origin.stationId, "002");
  assert.throws(() => selectOriginStation(state, "outside"), /within the walking limit/);
});

test("changing a walking limit clears only that side snap result", () => {
  let state = setAddress(createAddressSelection(), "origin", originAddress);
  state = setSnapCandidates(state, "origin", {
    candidates,
    minimumDistanceMeters: 240,
  });

  state = setWalkLimit(state, "origin", 1_200);

  assert.equal(state.origin.maxWalkMeters, 1_200);
  assert.deepEqual(state.origin.candidates, []);
  assert.equal(state.origin.stationId, null);
  assert.equal(state.destination.maxWalkMeters, 800);
});

test("walking limit accepts any whole metre inside the supported interval", () => {
  const state = setWalkLimit(createAddressSelection(), "origin", 847);

  assert.equal(state.origin.maxWalkMeters, 847);
});

test("an unavailable snap keeps the minimum distance needed for feedback", () => {
  let state = setAddress(createAddressSelection(), "destination", destinationAddress);

  state = setSnapUnavailable(state, "destination", 1_100);

  assert.deepEqual(state.destination.candidates, []);
  assert.equal(state.destination.stationId, null);
  assert.equal(state.destination.minimumDistanceMeters, 1_100);
});

for (const invalid of [0, 99, 100.5, 2_001]) {
  test(`walking limit rejects ${invalid}`, () => {
    assert.throws(
      () => setWalkLimit(createAddressSelection(), "origin", invalid),
      /between 100 and 2000 metres/,
    );
  });
}

test("route query requires origin address, valid origin station and destination address", () => {
  let state = createAddressSelection();
  assert.ok(validateAddressSelection(state).errors.origin);
  assert.ok(validateAddressSelection(state).errors.destination);

  state = setAddress(state, "origin", originAddress);
  state = setSnapCandidates(state, "origin", {
    candidates,
    minimumDistanceMeters: 240,
  });
  state = setAddress(state, "destination", destinationAddress);
  assert.ok(validateAddressSelection(state).errors.destination);
  state = setSnapCandidates(state, "destination", {
    candidates,
    minimumDistanceMeters: 240,
  });

  assert.deepEqual(validateAddressSelection(state), {
    errors: {},
    query: {
      mode: "address",
      origin: {
        ...originAddress,
        maxWalkMeters: 800,
        stationId: "001",
      },
      destination: {
        ...destinationAddress,
        maxWalkMeters: 800,
      },
      departureTime: "07:45",
    },
  });
});
