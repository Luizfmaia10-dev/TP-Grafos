const ERROR_KINDS = new Map([[404, "unknown-station"], [422, "invalid"], [503, "unavailable"]]);

export class ApiError extends Error {
  constructor(kind, status, message, detail = null) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
    this.detail = detail;
  }
}

async function readJson(response) {
  const payload = await response.json();
  if (!response.ok) {
    const detail = payload?.detail ?? null;
    const code = typeof detail === "object" ? detail?.code : null;
    const kind = code === "no_station_within_limit" ? "no-station"
      : code === "snap_distance_out_of_range" ? "invalid-limit"
        : ERROR_KINDS.get(response.status) ?? "http";
    throw new ApiError(kind, response.status, response.statusText, detail);
  }
  return payload;
}

function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function mapStation(station) {
  if (!isNonEmptyString(station.station_id) || !isNonEmptyString(station.name)
      || !Number.isFinite(station.latitude) || !Number.isFinite(station.longitude)) {
    throw new Error("Invalid station response");
  }
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
  if (typeof step.route_id !== "string" || !isNonEmptyString(step.vehicle_type)
      || !isNonEmptyString(step.departure_time) || !isNonEmptyString(step.arrival_time)
      || ![step.waiting_seconds, step.travel_seconds, step.distance_km].every(Number.isFinite)) {
    throw new Error("Invalid route step response");
  }
  const mapped = {
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
  if (isNonEmptyString(step.route_short_name)) {
    mapped.routeShortName = step.route_short_name;
  }
  return mapped;
}

function mapRouteResponse(payload, query) {
  if (!["found", "no-route"].includes(payload.status) || !isNonEmptyString(payload.service_date)) {
    throw new Error("Invalid route response");
  }
  const state = {
    status: payload.status,
    serviceDate: payload.service_date,
    origin: mapStation(payload.origin),
    destination: mapStation(payload.destination),
    query,
  };
  if (payload.status === "no-route") return state;
  const route = payload.route;
  if (!isNonEmptyString(route.arrival_time)
      || ![route.total_seconds, route.waiting_seconds, route.travel_seconds, route.distance_km].every(Number.isFinite)
      || !Array.isArray(route.steps) || !Array.isArray(route.instructions)
      || !route.instructions.every(instruction => typeof instruction === "string")) {
    throw new Error("Invalid route result response");
  }
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

function routePayload(query) {
  if (query.mode !== "address") {
    return {
      origin_id: query.originId,
      destination_id: query.destinationId,
      departure_time: query.departureTime,
    };
  }
  return {
    mode: "address",
    origin: {
      label: query.origin.label,
      latitude: query.origin.latitude,
      longitude: query.origin.longitude,
      max_walk_meters: query.origin.maxWalkMeters,
      station_id: query.origin.stationId,
    },
    destination: {
      label: query.destination.label,
      latitude: query.destination.latitude,
      longitude: query.destination.longitude,
      max_walk_meters: query.destination.maxWalkMeters,
    },
    departure_time: query.departureTime,
  };
}

export function createApi(fetchImpl = globalThis.fetch) {
  return {
    async getGeocodingConfig({ signal } = {}) {
      const payload = await readJson(await fetchImpl("/config/geocoding", { signal }));
      if (typeof payload.available !== "boolean"
          || !(typeof payload.api_key === "string" || payload.api_key === null)) {
        throw new Error("Invalid geocoding configuration response");
      }
      return { apiKey: payload.api_key, available: payload.available };
    },
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
        body: JSON.stringify(routePayload(query)),
      });
      return mapRouteResponse(await readJson(response), query);
    },
    async listSnapCandidates(point, { signal } = {}) {
      const response = await fetchImpl("/snap/candidates", {
        method: "POST", signal,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          latitude: point.latitude,
          longitude: point.longitude,
          max_walk_meters: point.maxWalkMeters,
        }),
      });
      const payload = await readJson(response);
      if (!Number.isInteger(payload.minimum_distance_meters)
          || !Array.isArray(payload.candidates)) {
        throw new Error("Invalid snap candidates response");
      }
      return {
        minimumDistanceMeters: payload.minimum_distance_meters,
        candidates: payload.candidates.map(candidate => ({
          station: mapStation(candidate.station),
          distanceMeters: candidate.distance_meters,
        })),
      };
    },
  };
}

const api = createApi();
export const listStations = api.listStations;
export const searchRoute = api.searchRoute;
export const getGeocodingConfig = api.getGeocodingConfig;
export const listSnapCandidates = api.listSnapCandidates;
