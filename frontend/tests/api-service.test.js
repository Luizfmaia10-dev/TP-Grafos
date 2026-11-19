import assert from "node:assert/strict";
import test from "node:test";
import { ApiError, createApi } from "../js/api-service.js";

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

test("station search defaults to twenty results and preserves an empty response", async () => {
  let requestedUrl;
  const api = createApi(async url => {
    requestedUrl = url;
    return Response.json([]);
  });

  assert.deepEqual(await api.listStations(""), []);
  assert.equal(requestedUrl, "/stations?query=&limit=20");
});

const query = { originId: "001", destinationId: "004", departureTime: "25:05" };
const central = { station_id: "001", name: "Central", latitude: -19.9, longitude: -43.9 };
const transfer = { station_id: "002", name: "Transfer", latitude: -19.901, longitude: -43.901 };
const terminal = { station_id: "003", name: "Terminal", latitude: -19.902, longitude: -43.902 };
const destination = { station_id: "004", name: "Destination", latitude: -19.903, longitude: -43.903 };
const normalizedCentral = {
  stationId: "001", name: "Central", label: "Central", mapName: "Central", shortName: "Central",
  latitude: -19.9, longitude: -43.9,
};
const normalizedTransfer = {
  stationId: "002", name: "Transfer", label: "Transfer", mapName: "Transfer", shortName: "Transfer",
  latitude: -19.901, longitude: -43.901,
};
const normalizedTerminal = {
  stationId: "003", name: "Terminal", label: "Terminal", mapName: "Terminal", shortName: "Terminal",
  latitude: -19.902, longitude: -43.902,
};
const normalizedDestination = {
  stationId: "004", name: "Destination", label: "Destination", mapName: "Destination", shortName: "Destination",
  latitude: -19.903, longitude: -43.903,
};

test("route search posts the service-day query and normalizes every travel mode", async () => {
  const calls = [];
  const instructions = [
    "Wait at Central until 25:06:00.",
    "Take BUS bus from Central to Transfer at 25:06:00; arrive at 25:11:30.",
    "Wait at Transfer until 25:13:00.",
    "Take SUBWAY metro from Transfer to Terminal at 25:13:00; arrive at 25:17:15.",
    "Take WALK walk from Terminal to Destination at 25:17:15; arrive at 25:19:30.",
  ];
  const api = createApi(async (url, options) => {
    calls.push({ url, options });
    return Response.json({
      status: "found", service_date: "2026-11-19", origin: central, destination,
      departure_time: "25:05",
      route: {
        arrival_time: "25:19:30", total_seconds: 870, waiting_seconds: 150,
        travel_seconds: 720, distance_km: 3.2, instructions,
        steps: [
          { origin: central, destination: transfer, route_id: "bus", vehicle_type: "BUS",
            departure_time: "25:06:00", arrival_time: "25:11:30", waiting_seconds: 60,
            travel_seconds: 330, distance_km: 1 },
          { origin: transfer, destination: terminal, route_id: "metro", vehicle_type: "SUBWAY",
            departure_time: "25:13:00", arrival_time: "25:17:15", waiting_seconds: 90,
            travel_seconds: 255, distance_km: 2 },
          { origin: terminal, destination, route_id: "walk", vehicle_type: "WALK",
            departure_time: "25:17:15", arrival_time: "25:19:30", waiting_seconds: 0,
            travel_seconds: 135, distance_km: 0.2 },
        ],
      },
    });
  });
  const signal = new AbortController().signal;

  const result = await api.searchRoute(query, { signal });

  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "/routes/search");
  assert.equal(calls[0].options.method, "POST");
  assert.deepEqual(calls[0].options.headers, { "content-type": "application/json" });
  assert.equal(calls[0].options.signal, signal);
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    origin_id: "001", destination_id: "004", departure_time: "25:05",
  });
  assert.deepEqual(result, {
    status: "found", serviceDate: "2026-11-19", origin: normalizedCentral,
    destination: normalizedDestination, query, arrivalTime: "25:19:30", totalSeconds: 870,
    waitingSeconds: 150, travelSeconds: 720, distanceKm: 3.2, instructions,
    steps: [
      { origin: normalizedCentral, destination: normalizedTransfer, routeId: "bus", vehicleType: "BUS",
        departureTime: "25:06:00", arrivalTime: "25:11:30", waitingSeconds: 60,
        travelSeconds: 330, distanceKm: 1 },
      { origin: normalizedTransfer, destination: normalizedTerminal, routeId: "metro", vehicleType: "SUBWAY",
        departureTime: "25:13:00", arrivalTime: "25:17:15", waitingSeconds: 90,
        travelSeconds: 255, distanceKm: 2 },
      { origin: normalizedTerminal, destination: normalizedDestination, routeId: "walk", vehicleType: "WALK",
        departureTime: "25:17:15", arrivalTime: "25:19:30", waitingSeconds: 0,
        travelSeconds: 135, distanceKm: 0.2 },
    ],
  });
  assert.equal(result.query, query);
});

test("a no-route response preserves endpoints and query without route fields", async () => {
  const api = createApi(async () => Response.json({
    status: "no-route", service_date: "2026-11-19", origin: central, destination,
    departure_time: "25:05", route: null,
  }));

  const result = await api.searchRoute(query);

  assert.deepEqual(result, {
    status: "no-route", serviceDate: "2026-11-19", origin: normalizedCentral,
    destination: normalizedDestination, query,
  });
  assert.equal(result.query, query);
});

for (const [status, kind] of [[404, "unknown-station"], [422, "invalid"], [503, "unavailable"], [500, "http"]]) {
  for (const method of ["listStations", "searchRoute"]) {
    test(`${method} classifies HTTP ${status} as ${kind}`, async () => {
      const api = createApi(async () => Response.json({ detail: "Request failed" }, { status }));

      await assert.rejects(() => api[method](method === "listStations" ? "Central" : query),
        error => error instanceof ApiError && error.kind === kind && error.status === status);
    });
  }
}

test("fetch failures retain their original identity", async () => {
  const failure = new TypeError("Failed to fetch");
  const api = createApi(async () => { throw failure; });

  await assert.rejects(() => api.searchRoute(query), error => error === failure);
});

test("invalid JSON remains an ordinary error", async () => {
  const api = createApi(async () => new Response("invalid JSON", { status: 200 }));

  await assert.rejects(() => api.searchRoute(query),
    error => error instanceof SyntaxError && !(error instanceof ApiError));
});
