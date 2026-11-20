const MAP_LAYOUTS = {
  desktop: { width: 960, height: 780, west: -44.045, east: -43.861, north: -19.803, south: -19.968 },
  mobile: { width: 358, height: 256, west: -44.018, east: -43.895, north: -19.814, south: -19.955 },
};
const MARKER_LETTERS = { origin: "A", destination: "B", both: "A/B" };
const MODE_LABELS = { bus: "Ônibus", subway: "Metrô", walk: "Caminhada" };

/** Native pixel coordinates in the matching Figma SVG, before responsive scaling. */
export function projectStation(station, layout) {
  const bounds = MAP_LAYOUTS[layout];
  return {
    x: (station.longitude - bounds.west) / (bounds.east - bounds.west) * bounds.width,
    y: (bounds.north - station.latitude) / (bounds.north - bounds.south) * bounds.height,
  };
}

export function fitRouteViewport(steps, layout, padding = 24) {
  const { width, height } = MAP_LAYOUTS[layout];
  const base = { x: 0, y: 0, width, height };
  if (steps.length === 0) return base;
  let left = Infinity;
  let top = Infinity;
  let right = -Infinity;
  let bottom = -Infinity;
  for (const step of steps) {
    for (const station of [step.origin, step.destination]) {
      const point = projectStation(station, layout);
      left = Math.min(left, point.x);
      top = Math.min(top, point.y);
      right = Math.max(right, point.x);
      bottom = Math.max(bottom, point.y);
    }
  }
  if (left >= 0 && top >= 0 && right <= width && bottom <= height) return base;
  left = Math.min(0, left - padding);
  top = Math.min(0, top - padding);
  right = Math.max(width, right + padding);
  bottom = Math.max(height, bottom + padding);
  const fittedWidth = Math.max(right - left, (bottom - top) * width / height);
  const fittedHeight = fittedWidth * height / width;
  return {
    x: left - (fittedWidth - (right - left)) / 2,
    y: top - (fittedHeight - (bottom - top)) / 2,
    width: fittedWidth,
    height: fittedHeight,
  };
}

export function buildRouteSegments(steps, layout) {
  return steps.map(step => ({
    mode: step.vehicleType.toLowerCase(),
    points: [step.origin, step.destination].map(station => {
      const point = projectStation(station, layout);
      return `${point.x},${point.y}`;
    }).join(" "),
  }));
}

export function currentMapStations(previous, suggestions, selection, result) {
  const selectedIds = new Set([selection.originId, selection.destinationId]);
  const routeStations = result
    ? [result.origin, result.destination, ...result.steps.flatMap(step => [step.origin, step.destination])]
    : [];
  return [...new Map([
    ...previous.filter(station => selectedIds.has(station.stationId)),
    ...suggestions, ...routeStations,
  ].map(station => [station.stationId, station])).values()];
}

export function createStationMap(container, onSelect) {
  const document = container.ownerDocument;
  let controls = [];

  function createControl(station) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "map-station";
    button.dataset.stationId = station.stationId;
    button.addEventListener("click", () => onSelect(station));

    const marker = document.createElement("span");
    marker.className = "map-marker";
    marker.setAttribute("aria-hidden", "true");
    const point = document.createElement("img");
    point.src = "/assets/icons/stop-origin.svg";
    point.alt = "";
    point.width = 17;
    point.height = 17;
    const letter = document.createElement("span");
    letter.className = "map-letter font-mono";
    marker.append(point, letter);

    const label = document.createElement("span");
    label.className = "map-label";
    label.setAttribute("aria-hidden", "true");
    const name = document.createElement("span");
    name.className = "map-stop-name font-semibold";
    const desktopName = document.createElement("span");
    desktopName.className = "station-name--desktop";
    desktopName.textContent = station.mapName;
    const mobileName = document.createElement("span");
    mobileName.className = "station-name--mobile";
    mobileName.textContent = station.shortName;
    name.append(desktopName, mobileName);
    const detail = document.createElement("span");
    detail.className = "map-stop-detail text-rg-map-muted";
    detail.textContent = station.platform ? `Plataforma ${station.platform}` : "";
    detail.hidden = !station.platform;
    label.append(name, detail);
    button.append(marker, label);
    return { station, button, point, letter, label, desktopName, mobileName };
  }

  const layer = container.parentElement;
  let view = null;

  function render() {
    if (!view) return;
    const { selection, activeField, result } = view;
    const layout = window.matchMedia("(width < 960px)").matches ? "mobile" : "desktop";
    const size = MAP_LAYOUTS[layout];
    const steps = result?.steps ?? [];
    const viewport = fitRouteViewport(steps, layout);
    const panelElement = layer.parentElement;
    panelElement.dataset.routeResult = String(Boolean(result));
    const panel = panelElement.getBoundingClientRect();
    const markerSize = result ? controls.reduce((maximum, { button }) => {
      const marker = button.getBoundingClientRect();
      return Math.max(maximum, marker.width, marker.height);
    }, 0) : 0;
    const layerScale = Math.min((panel.width - markerSize) / size.width, (panel.height - markerSize) / size.height);
    // Reserve half a marker on every side of the contained coordinate plane.
    layer.style.width = result ? `${size.width * layerScale}px` : "";
    layer.style.height = result ? `${size.height * layerScale}px` : "";
    const scale = layer.clientWidth / viewport.width;
    const backgroundScale = size.width / viewport.width;
    const background = layer.querySelector(".network-background");
    background.style.transformOrigin = "top left";
    background.style.transform = `matrix(${backgroundScale}, 0, 0, ${backgroundScale}, ${-viewport.x * scale}, ${-viewport.y * scale})`;
    layer.querySelector(`.network-image--${layout}`).style.transform = `scale(${layer.clientWidth / size.width})`;
    const route = document.querySelector("#map-route");
    const legend = document.querySelector("#map-key-route");
    const segments = buildRouteSegments(steps, layout);
    route.setAttribute("viewBox", `${viewport.x} ${viewport.y} ${viewport.width} ${viewport.height}`);
    route.toggleAttribute("hidden", !result);
    route.replaceChildren(...segments.flatMap(segment => ["route-glow", "route-line"].map(className => {
      const line = route.ownerDocument.createElementNS("http://www.w3.org/2000/svg", "polyline");
      line.setAttribute("points", segment.points);
      line.setAttribute("class", `${className} route-segment--${segment.mode}`);
      line.setAttribute("fill", "none");
      line.setAttribute("stroke-linecap", segment.mode === "walk" ? "butt" : "round");
      return line;
    })));
    document.querySelector("#map-key-station").hidden = Boolean(result);
    legend.hidden = !result;
    legend.replaceChildren(...[...new Set(segments.map(segment => segment.mode))].map(mode => {
      const item = document.createElement("span");
      item.className = "map-key-mode";
      item.dataset.mode = mode;
      const line = document.createElement("span");
      line.className = `route-key-line route-segment--${mode}`;
      line.setAttribute("aria-hidden", "true");
      const label = document.createElement("span");
      label.textContent = MODE_LABELS[mode];
      item.append(line, label);
      return item;
    }));
    document.querySelector("#map-key-label").hidden = Boolean(result);
    document.querySelector("#map-key-short").hidden = Boolean(result);
    const routeStationIds = new Set(result
      ? [result.origin, result.destination, ...result.steps.flatMap(step => [step.origin, step.destination])]
        .map(station => station.stationId)
      : []);
    let dense = false;
    if (result) {
      const first = projectStation(result.origin, layout);
      const last = projectStation(result.destination, layout);
      // Nearby vertices retain their real coordinates; their labels carry A/B.
      dense = Math.hypot(last.x - first.x, last.y - first.y) * scale < 44;
    }
    container.dataset.dense = String(dense);
    for (const { station, button, point, letter, label, desktopName, mobileName } of controls) {
      const position = projectStation(station, layout);
      button.style.left = `${(position.x - viewport.x) * 100 / viewport.width}%`;
      button.style.top = `${(position.y - viewport.y) * 100 / viewport.height}%`;
      const isOrigin = station.stationId === selection.originId;
      const isDestination = station.stationId === selection.destinationId;
      const selected = isOrigin || isDestination;
      let role = "";
      if (isOrigin) role = "origin";
      if (isDestination) role = "destination";
      if (isOrigin && isDestination) role = "both";

      button.dataset.selection = role;
      button.dataset.onRoute = String(routeStationIds.has(station.stationId));
      button.disabled = Boolean(result) || activeField === null;
      button.setAttribute("aria-pressed", String(selected));
      button.setAttribute("aria-label", result
        ? `${station.label}${isOrigin ? ", origem" : isDestination ? ", destino" : ""}`
        : activeField === null
          ? `${station.label}. Escolha primeiro o campo de origem ou destino.`
          : `Selecionar ${station.label} como ${activeField === "origin" ? "origem" : "destino"}`);
      point.hidden = selected || Boolean(result);
      letter.hidden = !selected;
      letter.textContent = MARKER_LETTERS[role] ?? "";
      const prefix = dense && selected ? `${MARKER_LETTERS[role]} · ` : "";
      desktopName.textContent = prefix + station.mapName;
      mobileName.textContent = prefix + station.shortName;
      label.style.transform = "";
    }
    // Keep labels inside the visible crop without moving their geographic vertices.
    const placed = [];
    for (const { label } of controls) {
      if (label.getClientRects().length === 0) continue;
      const rect = label.getBoundingClientRect();
      const x = Math.max(panel.left + 12 - rect.left, Math.min(0, panel.right - 12 - rect.right));
      let y = 0;
      for (const previous of placed) {
        if (rect.left + x < previous.right + 14 && rect.right + x > previous.left - 14
          && rect.top + y < previous.bottom + 14 && rect.bottom + y > previous.top - 14) {
          y = previous.bottom + 14 - rect.top;
        }
      }
      label.style.transform = `translate(${x}px, ${y}px)`;
      placed.push({ left: rect.left + x, right: rect.right + x, top: rect.top + y, bottom: rect.bottom + y });
    }
  }

  new ResizeObserver(render).observe(layer.parentElement);
  return {
    setStations(stations) {
      const nextStations = [...new Map(stations.map(station => [station.stationId, station])).values()];
      if (controls.length === nextStations.length
        && controls.every((control, index) => control.station.stationId === nextStations[index].stationId)) {
        render();
        return;
      }
      controls = nextStations.map(createControl);
      container.replaceChildren(...controls.map(control => control.button));
      render();
    },
    update(selection, activeField, result = null) {
      view = { selection, activeField, result };
      render();
    },
  };
}
