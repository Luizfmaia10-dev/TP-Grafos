import assert from "node:assert/strict";
import test from "node:test";
import { DEMO_STATIONS, DEMO_TRIP } from "../js/demo-data.js";
import { buildDemoRoute, searchDemoRoute } from "../js/demo-service.js";

const [pampulha, rio, parana] = DEMO_STATIONS;
const query = {
  originId: pampulha.stationId,
  destinationId: parana.stationId,
  departureTime: "07:45",
};

test("the reference trip preserves waiting, vehicle and total seconds", () => {
  const result = buildDemoRoute(query);
  assert.equal(result.status, "found");
  assert.equal(result.waitingSeconds, 360);
  assert.equal(result.vehicleSeconds, 1756);
  assert.equal(result.totalSeconds, 2116);
  assert.equal(result.totalSeconds, result.waitingSeconds + result.vehicleSeconds);
  assert.equal(result.boardingTime, "07:51:00");
  assert.equal(result.arrivalTime, "08:20:16");
  assert.equal(result.query.departureTime, "07:45");
  assert.equal(result.routeId, DEMO_TRIP.routeId);
  assert.equal(result.tripId, DEMO_TRIP.tripId);
  assert.equal(result.serviceId, DEMO_TRIP.serviceId);
  assert.equal(result.stops[1].arrivalTime, "08:16:51");
});

test("departure exactly at boarding is allowed without waiting", () => {
  const result = buildDemoRoute({ ...query, departureTime: "07:51" });
  assert.equal(result.status, "found");
  assert.equal(result.waitingSeconds, 0);
  assert.equal(result.totalSeconds, 1756);
});

for (const departureTime of ["07:52", "08:30", "25:00", "100:00"]) {
  test(`a missed sample departure at ${departureTime} does not wrap to another day`, () => {
    const result = buildDemoRoute({ ...query, departureTime });
    assert.equal(result.status, "no-route");
    assert.equal(result.boardingTime, "07:51:00");
    assert.equal(result.stops, undefined);
  });
}

test("hours and minutes stay unchanged in the input query", () => {
  const input = { ...query, departureTime: "07:45" };
  assert.equal(buildDemoRoute(input).query.departureTime, "07:45");
  assert.equal(input.departureTime, "07:45");
});

test("a forward subtrip uses its own boarding and arrival times", () => {
  const result = buildDemoRoute({
    ...query, originId: rio.stationId, departureTime: "08:16",
  });
  assert.equal(result.status, "found");
  assert.equal(result.waitingSeconds, 51);
  assert.equal(result.vehicleSeconds, 205);
  assert.equal(result.totalSeconds, 256);
  assert.deepEqual(result.stops.map(stop => stop.stationId), [rio.stationId, parana.stationId]);
  assert.equal(result.boardingTime, "08:16:51");
  assert.equal(result.arrivalTime, "08:20:16");
});

test("a shorter destination does not include the rest of the trip", () => {
  const result = buildDemoRoute({ ...query, destinationId: rio.stationId });
  assert.equal(result.arrivalTime, "08:16:51");
  assert.equal(result.vehicleSeconds, 1551);
  assert.deepEqual(result.stops.map(stop => stop.stationId), [pampulha.stationId, rio.stationId]);
});

for (const pair of [
  { originId: "unknown", destinationId: parana.stationId },
  { originId: pampulha.stationId, destinationId: "unknown" },
  { originId: parana.stationId, destinationId: pampulha.stationId },
  { originId: pampulha.stationId, destinationId: pampulha.stationId },
]) {
  test(`the unsupported pair ${pair.originId} -> ${pair.destinationId} is identified`, () => {
    assert.equal(buildDemoRoute({ ...query, ...pair }).status, "outside-sample");
  });
}

test("distance is the sum of geographic segments, not the direct endpoint distance", () => {
  const full = buildDemoRoute(query);
  const first = buildDemoRoute({ ...query, destinationId: rio.stationId });
  const second = buildDemoRoute({ ...query, originId: rio.stationId });
  assert.ok(Math.abs(full.distanceKm - 9.027936761925123) < 1e-9);
  assert.ok(Math.abs(full.distanceKm - first.distanceKm - second.distanceKm) < 1e-9);
});

test("invalid time input cannot produce a fabricated itinerary", () => {
  assert.throws(() => buildDemoRoute({ ...query, departureTime: "07:60" }), RangeError);
  assert.throws(() => buildDemoRoute({ ...query, departureTime: "07:45:00" }), RangeError);
});

test("the asynchronous query settles only after the loading interval", async () => {
  let settled = false;
  const pending = searchDemoRoute(query).then(result => { settled = true; return result; });
  await Promise.resolve();
  assert.equal(settled, false);
  assert.equal((await pending).status, "found");
});

test("an in-flight query can be aborted", async () => {
  const controller = new AbortController();
  const pending = searchDemoRoute(query, { signal: controller.signal });
  controller.abort();
  await assert.rejects(pending, { name: "AbortError" });
});

test("an already aborted query cannot start", async () => {
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(searchDemoRoute(query, { signal: controller.signal }), { name: "AbortError" });
});
