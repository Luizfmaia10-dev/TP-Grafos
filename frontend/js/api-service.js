const ERROR_KINDS = new Map([[404, "unknown-station"], [422, "invalid"], [503, "unavailable"]]);

export class ApiError extends Error {
  constructor(kind, status, message) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
  }
}

async function readJson(response) {
  if (!response.ok) {
    throw new ApiError(ERROR_KINDS.get(response.status) ?? "http", response.status, response.statusText);
  }
  return response.json();
}

function mapStation(station) {
  return {
    stationId: station.station_id,
    name: station.name,
    label: station.name,
    mapName: station.name,
    shortName: station.name,
    latitude: station.latitude,
    longitude: station.longitude,
  };
}

function mapStep(step) {
  return {
    origin: mapStation(step.origin),
    destination: mapStation(step.destination),
    routeId: step.route_id,
    vehicleType: step.vehicle_type,
    departureTime: step.departure_time,
    arrivalTime: step.arrival_time,
    waitingSeconds: step.waiting_seconds,
    travelSeconds: step.travel_seconds,
    distanceKm: step.distance_km,
  };
}

function mapRouteResponse(payload, query) {
  const state = {
    status: payload.status,
    serviceDate: payload.service_date,
    origin: mapStation(payload.origin),
    destination: mapStation(payload.destination),
    query,
  };
  if (payload.status === "no-route") return state;
  const route = payload.route;
  return {
    ...state,
    arrivalTime: route.arrival_time,
    totalSeconds: route.total_seconds,
    waitingSeconds: route.waiting_seconds,
    travelSeconds: route.travel_seconds,
    distanceKm: route.distance_km,
    steps: route.steps.map(mapStep),
    instructions: route.instructions,
  };
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
