export function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  if (minutes === 0 && remainder > 0) return `${remainder} s`;
  return `${minutes} min${remainder ? ` ${remainder} s` : ""}`;
}

const MODALS = {
  BUS: { kind: "bus", label: "Ônibus" },
  SUBWAY: { kind: "subway", label: "Metrô" },
  WALK: { kind: "walk", label: "Caminhada" },
};

export function buildTimelineEntries(result) {
  const entries = [{
    kind: "origin", time: result.query.departureTime, station: result.origin,
    title: result.origin.name, description: "Início da viagem",
  }];
  let instructionIndex = 0;
  for (const step of result.steps) {
    if (step.waitingSeconds > 0) {
      entries.push({
        kind: "wait", time: step.departureTime, station: step.origin,
        title: `Espera · ${formatDuration(step.waitingSeconds)}`,
        description: result.instructions[instructionIndex++],
      });
    }
    const modal = MODALS[step.vehicleType];
    entries.push({
      ...step, ...modal, time: step.departureTime, station: step.origin,
      title: modal.kind === "walk" ? modal.label : `${modal.label} · ${step.routeId}`,
      description: result.instructions[instructionIndex++],
    });
  }
  entries.push({
    kind: "destination", time: result.arrivalTime, station: result.destination,
    title: result.destination.name, description: "Chegada ao destino",
  });
  return entries;
}

function timelineStep(time, station, title, description, kind) {
  const row = document.createElement("li");
  row.className = `itinerary-step itinerary-step--${kind}`;
  row.dataset.stationId = station.stationId;
  const clock = document.createElement("span");
  clock.className = "step-time font-mono";
  // GTFS service-day hours can exceed 23, unlike an HTML time datetime value.
  clock.textContent = time.replace(/^(\d+:\d{2}):\d{2}$/, "$1");
  clock.title = time;
  clock.setAttribute("aria-label", time);
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
  arrival.textContent = result.arrivalTime.replace(/^(\d+:\d{2}):\d{2}$/, "$1");
  document.querySelector("#exact-arrival").textContent = result.arrivalTime;
  arrival.title = result.arrivalTime;
  document.querySelector("#waiting-duration").textContent = `${formatDuration(result.waitingSeconds)} de espera`;
  document.querySelector("#vehicle-duration").textContent = `${formatDuration(result.travelSeconds)} em deslocamento`;
  document.querySelector("#waiting-proportion").style.width = `${result.waitingSeconds / result.totalSeconds * 100}%`;
  document.querySelector("#route-distance").textContent = `≈ ${result.distanceKm.toLocaleString("pt-BR", {
    minimumFractionDigits: 1, maximumFractionDigits: 1,
  })} km`;

  const steps = buildTimelineEntries(result).map(entry => timelineStep(
    entry.time, entry.station, entry.title, entry.description, entry.kind,
  ));
  document.querySelector("#itinerary-steps").replaceChildren(...steps);
}
