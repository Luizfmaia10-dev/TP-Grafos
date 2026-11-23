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

test("geocoding configuration exposes only the public browser key and availability", async () => {
  const api = createApi(async url => {
    assert.equal(url, "/config/geocoding");
    return Response.json({ api_key: "browser-key", available: true });
  });

  assert.deepEqual(await api.getGeocodingConfig(), {
    apiKey: "browser-key",
    available: true,
  });
});

test("snap candidate search serializes coordinates and normalizes distances", async () => {
  const calls = [];
  const api = createApi(async (url, options) => {
    calls.push({ url, options });
    return Response.json({
      minimum_distance_meters: 240,
      count: 1,
      candidates: [{ station: central, distance_meters: 240 }],
    });
  });

  const result = await api.listSnapCandidates({
    latitude: -19.9,
    longitude: -43.9,
    maxWalkMeters: 800,
  });

  assert.equal(calls[0].url, "/snap/candidates");
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    latitude: -19.9,
    longitude: -43.9,
    max_walk_meters: 800,
  });
  assert.equal(result.minimumDistanceMeters, 240);
  assert.equal(result.candidates[0].station.stationId, "001");
  assert.equal(result.candidates[0].distanceMeters, 240);
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
          { origin: central, destination: transfer, route_id: "bus", route_short_name: "510",
            vehicle_type: "BUS",
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
      { origin: normalizedCentral, destination: normalizedTransfer, routeId: "bus",
        routeShortName: "510", vehicleType: "BUS",
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

test("address route search keeps destination on the page and origin station in its modal", async () => {
  const calls = [];
  const addressQuery = {
    mode: "address",
    origin: {
      label: "Rua A",
      latitude: -19.9,
      longitude: -43.9,
      maxWalkMeters: 800,
      stationId: "001",
    },
    destination: {
      label: "Rua B",
      latitude: -19.91,
      longitude: -43.91,
      maxWalkMeters: 1_200,
    },
    departureTime: "07:45",
  };
  const api = createApi(async (url, options) => {
    calls.push({ url, options });
    return Response.json({
      status: "no-route",
      service_date: "2026-11-17",
      origin: central,
      destination,
      departure_time: "07:45",
      route: null,
    });
  });

  await api.searchRoute(addressQuery);

  assert.deepEqual(JSON.parse(calls[0].options.body), {
    mode: "address",
    origin: {
      label: "Rua A",
      latitude: -19.9,
      longitude: -43.9,
      max_walk_meters: 800,
      station_id: "001",
    },
    destination: {
      label: "Rua B",
      latitude: -19.91,
      longitude: -43.91,
      max_walk_meters: 1_200,
    },
    departure_time: "07:45",
  });
});

test("structured snap errors preserve their detail", async () => {
  const api = createApi(async () => Response.json({
    detail: { code: "no_station_within_limit", minimum_distance_meters: 340 },
  }, { status: 404 }));

  await assert.rejects(
    () => api.listSnapCandidates({ latitude: 0, longitude: 0, maxWalkMeters: 100 }),
    error => error instanceof ApiError
      && error.detail.code === "no_station_within_limit"
      && error.detail.minimum_distance_meters === 340,
  );
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

const completeStep = {
  origin: central, destination, route_id: "bus", vehicle_type: "BUS",
  departure_time: "25:06:00", arrival_time: "25:11:30", waiting_seconds: 60,
  travel_seconds: 330, distance_km: 1,
};
const completeRoute = {
  arrival_time: "25:11:30", total_seconds: 390, waiting_seconds: 60,
  travel_seconds: 330, distance_km: 1, steps: [completeStep], instructions: ["Take BUS bus."],
};
const completeResponse = {
  status: "found", service_date: "2026-11-19", origin: central, destination,
  departure_time: "25:05", route: completeRoute,
};

for (const [description, route] of [
  ["missing arrival and totals", { steps: [], instructions: [] }],
  ["missing arrival time", { ...completeRoute, arrival_time: undefined }],
  ["missing total seconds", { ...completeRoute, total_seconds: undefined }],
  ["missing waiting seconds", { ...completeRoute, waiting_seconds: undefined }],
  ["missing travel seconds", { ...completeRoute, travel_seconds: undefined }],
  ["missing distance", { ...completeRoute, distance_km: undefined }],
  ["non-numeric totals", { ...completeRoute, total_seconds: "390" }],
  ["missing instructions", { ...completeRoute, instructions: undefined }],
  ["non-array instructions", { ...completeRoute, instructions: "Take BUS bus." }],
  ["non-text instruction", { ...completeRoute, instructions: [null] }],
]) {
  test(`a found response rejects ${description} as an ordinary error`, async () => {
    const api = createApi(async () => Response.json({ ...completeResponse, route }));

    await assert.rejects(() => api.searchRoute(query),
      error => error instanceof Error && !(error instanceof ApiError));
  });
}

for (const field of ["station_id", "name", "latitude", "longitude"]) {
  test(`station search rejects a station missing ${field}`, async () => {
    const api = createApi(async () => Response.json([{ ...central, [field]: undefined }]));

    await assert.rejects(() => api.listStations("Central"),
      error => error instanceof Error && !(error instanceof ApiError));
  });
}

for (const [description, payload] of [
  ["missing service date", { ...completeResponse, service_date: undefined }],
  ["unknown status", { ...completeResponse, status: "ready" }],
  ["endpoint without ID", { ...completeResponse, origin: { ...central, station_id: undefined } }],
  ["no-route endpoint without name", { ...completeResponse, status: "no-route", route: null,
    destination: { ...destination, name: undefined } }],
  ["step station without name", { ...completeResponse, route: { ...completeRoute,
    steps: [{ ...completeStep, destination: { ...destination, name: undefined } }] } }],
]) {
  test(`route search rejects ${description} as an ordinary error`, async () => {
    const api = createApi(async () => Response.json(payload));

    await assert.rejects(() => api.searchRoute(query),
      error => error instanceof Error && !(error instanceof ApiError));
  });
}

for (const field of ["route_id", "vehicle_type", "departure_time", "arrival_time", "waiting_seconds", "travel_seconds", "distance_km"]) {
  test(`route search rejects a step missing ${field}`, async () => {
    const api = createApi(async () => Response.json({ ...completeResponse,
      route: { ...completeRoute, steps: [{ ...completeStep, [field]: undefined }] },
    }));

    await assert.rejects(() => api.searchRoute(query),
      error => error instanceof Error && !(error instanceof ApiError));
  });
}
