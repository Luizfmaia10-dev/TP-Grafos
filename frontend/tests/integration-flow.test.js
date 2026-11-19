import assert from "node:assert/strict";
import test from "node:test";
import { createApi } from "../js/api-service.js";
import { createStationRequest } from "../js/station-request.js";
import { createRouteRequest } from "../js/route-request.js";
import { createSelection, selectStation, validateSelection } from "../js/selection.js";
import { buildTimelineEntries } from "../js/route-view.js";
import { buildRouteSegments } from "../js/map.js";

test("station search and confirmed selection produce a normalized itinerary and map route", async () => {
  const origin = { station_id: "001", name: "Central", latitude: -19.9, longitude: -43.95 };
  const destination = { station_id: "002", name: "Terminal", latitude: -19.91, longitude: -43.94 };
  const api = createApi(async (url, options) => {
    if (url.startsWith("/stations?")) {
      const query = new URL(url, "http://localhost").searchParams.get("query");
      return Response.json(query === "central" ? [origin] : [destination]);
    }
    assert.equal(url, "/routes/search");
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), {
      origin_id: "001", destination_id: "002", departure_time: "07:45",
    });
    return Response.json({
      status: "found", service_date: "2026-11-19", origin, destination,
      route: {
        arrival_time: "07:55:00", total_seconds: 600, waiting_seconds: 0,
        travel_seconds: 600, distance_km: 1.5, instructions: ["Siga até Terminal."],
        steps: [{ origin, destination, route_id: "bus", vehicle_type: "BUS",
          departure_time: "07:45:00", arrival_time: "07:55:00", waiting_seconds: 0,
          travel_seconds: 600, distance_km: 1.5 }],
      },
    });
  });
  const stationStates = [];
  const stationRequest = createStationRequest(api.listStations, state => stationStates.push(state.status));
  const routeStates = [];
  const routeRequest = createRouteRequest(api.searchRoute, state => routeStates.push(state.status));
  await stationRequest.submit("central");
  let selection = selectStation(createSelection(), "origin", stationRequest.state.stations[0]);
  await stationRequest.submit("terminal");
  selection = selectStation(selection, "destination", stationRequest.state.stations[0]);
  await routeRequest.submit(validateSelection(selection).query);
  assert.deepEqual(stationStates, ["loading", "ready", "loading", "ready"]);
  assert.deepEqual(routeStates, ["loading", "found"]);
  assert.equal(routeRequest.state.status, "found");
  assert.deepEqual(buildTimelineEntries(routeRequest.state).map(item => item.kind), ["origin", "bus", "destination"]);
  assert.equal(buildRouteSegments(routeRequest.state.steps, "desktop")[0].mode, "bus");
  routeRequest.cancel();
  assert.equal(routeRequest.state.status, "idle");
});
