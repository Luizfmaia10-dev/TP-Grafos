import { DEMO_STATIONS, DEMO_TRIP } from "./demo-data.js";
import { normalizeDepartureTime } from "./selection.js";

function timeToSeconds(time) {
  const [hours, minutes, seconds] = time.split(":").map(Number);
  return hours * 3600 + minutes * 60 + seconds;
}

/** Geographic segment length, not a street or GTFS shape distance. */
function segmentDistanceKm(origin, destination) {
  const radians = degrees => degrees * Math.PI / 180;
  const latitude = radians(destination.latitude - origin.latitude);
  const longitude = radians(destination.longitude - origin.longitude);
  const a = Math.sin(latitude / 2) ** 2
    + Math.cos(radians(origin.latitude)) * Math.cos(radians(destination.latitude))
    * Math.sin(longitude / 2) ** 2;
  return 6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/** Read a forward slice of one fixed trip; this is not the graph routing engine. */
export function buildDemoRoute(query) {
  const departureTime = normalizeDepartureTime(query.departureTime);
  if (departureTime === null) throw new RangeError("Invalid service-day time");

  const originIndex = DEMO_TRIP.stopTimes.findIndex(stop => stop.stationId === query.originId);
  const destinationIndex = DEMO_TRIP.stopTimes.findIndex(stop => stop.stationId === query.destinationId);
  if (originIndex < 0 || destinationIndex <= originIndex) return { status: "outside-sample" };

  const boardingTime = DEMO_TRIP.stopTimes[originIndex].departureTime;
  const departureSeconds = timeToSeconds(departureTime);
  const boardingSeconds = timeToSeconds(boardingTime);
  if (departureSeconds > boardingSeconds) return { status: "no-route", boardingTime };

  const stops = DEMO_TRIP.stopTimes.slice(originIndex, destinationIndex + 1).map(stop => ({
    ...DEMO_STATIONS.find(station => station.stationId === stop.stationId), ...stop,
  }));
  const arrivalTime = stops.at(-1).arrivalTime;
  const arrivalSeconds = timeToSeconds(arrivalTime);
  let distanceKm = 0;
  for (let index = 1; index < stops.length; index++) {
    distanceKm += segmentDistanceKm(stops[index - 1], stops[index]);
  }

  return {
    status: "found",
    routeId: DEMO_TRIP.routeId,
    routeShortName: DEMO_TRIP.routeShortName,
    tripId: DEMO_TRIP.tripId,
    serviceId: DEMO_TRIP.serviceId,
    query: { ...query, departureTime },
    boardingTime,
    arrivalTime,
    waitingSeconds: boardingSeconds - departureSeconds,
    vehicleSeconds: arrivalSeconds - boardingSeconds,
    totalSeconds: arrivalSeconds - departureSeconds,
    distanceKm,
    stops,
  };
}

/** A short local delay makes the loading state observable without a network call. */
export function searchDemoRoute(query, { signal } = {}) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("Query cancelled", "AbortError"));
      return;
    }
    const onAbort = () => {
      clearTimeout(timer);
      reject(new DOMException("Query cancelled", "AbortError"));
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      try {
        resolve(buildDemoRoute(query));
      } catch (error) {
        reject(error);
      }
    }, 500);
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}
