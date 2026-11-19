import assert from "node:assert/strict";
import test from "node:test";
import { createStationRequest } from "../js/station-request.js";

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

test("a station query reports loading and then its stations", async () => {
  const operation = deferred();
  const stations = [{ stationId: "2", label: "Central" }];
  const states = [];
  const request = createStationRequest((query, { signal }) => {
    assert.equal(query, "central");
    assert.ok(signal instanceof AbortSignal);
    return operation.promise;
  }, state => states.push(state));

  assert.deepEqual(request.state, { status: "idle" });
  const pending = request.submit("central");
  assert.deepEqual(request.state, { status: "loading", query: "central" });
  operation.resolve(stations);
  await pending;

  assert.deepEqual(request.state, { status: "ready", query: "central", stations });
  assert.deepEqual(states, [
    { status: "loading", query: "central" },
    { status: "ready", query: "central", stations },
  ]);
});

test("a query without stations reports an empty result", async () => {
  const states = [];
  const request = createStationRequest(async () => [], state => states.push(state));

  await request.submit("missing");

  assert.deepEqual(request.state, { status: "empty", query: "missing", stations: [] });
  assert.deepEqual(states, [
    { status: "loading", query: "missing" },
    { status: "empty", query: "missing", stations: [] },
  ]);
});

test("a failed query publishes its query and error", async () => {
  const error = new Error("Unavailable");
  const states = [];
  const request = createStationRequest(async () => { throw error; }, state => states.push(state));

  await request.submit("central");

  assert.deepEqual(request.state, { status: "error", query: "central", error });
  assert.deepEqual(states, [
    { status: "loading", query: "central" },
    { status: "error", query: "central", error },
  ]);
});

test("cancelling aborts the search and ignores a late response", async () => {
  const operation = deferred();
  const states = [];
  let signal;
  const request = createStationRequest((query, options) => {
    signal = options.signal;
    return operation.promise;
  }, state => states.push(state));

  const pending = request.submit("central");
  request.cancel();
  assert.equal(signal.aborted, true);
  assert.deepEqual(request.state, { status: "idle" });
  operation.resolve([{ stationId: "2", label: "Central" }]);
  await pending;

  assert.deepEqual(states, [{ status: "loading", query: "central" }, { status: "idle" }]);
  assert.deepEqual(request.state, { status: "idle" });
});

test("cancelling ignores an abort rejection", async () => {
  const states = [];
  const request = createStationRequest((query, { signal }) => new Promise((resolve, reject) => {
    signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
  }), state => states.push(state));

  const pending = request.submit("central");
  request.cancel();
  await pending;

  assert.deepEqual(states, [{ status: "loading", query: "central" }, { status: "idle" }]);
  assert.deepEqual(request.state, { status: "idle" });
});

test("an older station response cannot replace a newer query", async () => {
  const pending = new Map();
  const states = [];
  const request = createStationRequest(query => new Promise(resolve => pending.set(query, resolve)),
    state => states.push(state));
  const oldCall = request.submit("cent");
  const newCall = request.submit("central");
  pending.get("central")([{ stationId: "2", label: "Central" }]);
  await newCall;
  pending.get("cent")([{ stationId: "1", label: "Old" }]);
  await oldCall;

  assert.deepEqual(request.state, {
    status: "ready", query: "central", stations: [{ stationId: "2", label: "Central" }],
  });
  assert.deepEqual(states.filter(state => state.stations).map(state => state.query), ["central"]);
});

test("a new query aborts the previous search without publishing its failure", async () => {
  const states = [];
  let oldSignal;
  const request = createStationRequest((query, { signal }) => {
    if (query === "central") return Promise.resolve([{ stationId: "2", label: "Central" }]);
    oldSignal = signal;
    return new Promise((resolve, reject) => {
      signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
    });
  }, state => states.push(state));

  const oldCall = request.submit("cent");
  const newCall = request.submit("central");
  assert.equal(oldSignal.aborted, true);
  await Promise.all([oldCall, newCall]);

  assert.deepEqual(states.map(state => state.status), ["loading", "loading", "ready"]);
  assert.equal(request.state.query, "central");
});
