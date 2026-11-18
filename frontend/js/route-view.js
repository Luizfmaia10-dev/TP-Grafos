export function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  if (minutes === 0 && remainder > 0) return `${remainder} s`;
  return `${minutes} min${remainder ? ` ${remainder} s` : ""}`;
}

function timelineStep(time, station, title, description, kind) {
  const row = document.createElement("li");
  row.className = `itinerary-step itinerary-step--${kind}`;
  row.dataset.stationId = station.stationId;
  const clock = document.createElement("span");
  clock.className = "step-time font-mono";
  // GTFS service-day hours can exceed 23, unlike an HTML time datetime value.
  clock.textContent = time;
  const marker = document.createElement("span");
  marker.className = "step-marker font-mono";
  marker.setAttribute("aria-hidden", "true");
  marker.textContent = kind === "origin" ? "A" : kind === "destination" ? "B" : "";
  const copy = document.createElement("div");
  copy.className = "step-copy";
  const name = document.createElement("p");
  name.className = "step-title";
  name.textContent = title;
  const detail = document.createElement("p");
  detail.className = "step-description";
  detail.textContent = description;
  copy.append(name, detail);
  row.append(clock, marker, copy);
  return row;
}

export function renderRoute(result) {
  const total = document.querySelector("#total-minutes");
  total.textContent = Math.round(result.totalSeconds / 60);
  document.querySelector("#exact-total").textContent = `Tempo total exato: ${formatDuration(result.totalSeconds)}.`;
  const arrival = document.querySelector("#arrival-time");
  arrival.textContent = result.arrivalTime.slice(0, -3);
  arrival.setAttribute("aria-label", `Chegada prevista às ${result.arrivalTime}`);
  arrival.title = result.arrivalTime;
  document.querySelector("#waiting-duration").textContent = `${formatDuration(result.waitingSeconds)} de espera`;
  document.querySelector("#vehicle-duration").textContent = `${formatDuration(result.vehicleSeconds)} no ônibus`;
  document.querySelector("#waiting-proportion").style.width = `${result.waitingSeconds / result.totalSeconds * 100}%`;
  document.querySelector("#route-distance").textContent = `≈ ${result.distanceKm.toLocaleString("pt-BR", {
    minimumFractionDigits: 1, maximumFractionDigits: 1,
  })} km`;

  const origin = result.stops[0];
  const destination = result.stops.at(-1);
  const steps = [
    timelineStep(result.query.departureTime, origin, origin.mapName,
      `Chegue à plataforma ${origin.platform}`, "origin"),
    timelineStep(result.boardingTime, origin, `Embarque na linha ${result.routeShortName}`,
      "Ônibus · sentido Centro", "boarding"),
    ...result.stops.slice(1, -1).map(stop => timelineStep(stop.arrivalTime, stop,
      stop.mapName, `Passagem pela plataforma ${stop.platform}`, "intermediate")),
    timelineStep(result.arrivalTime, destination, destination.mapName,
      `Desembarque · ${destination.district}`, "destination"),
  ];
  document.querySelector("#itinerary-steps").replaceChildren(...steps);
}
