import { animateMapLayout } from "./map-expansion.js";

const MAP_LAYOUTS = {
  desktop: { width: 960, height: 780, west: -44.045, east: -43.861, north: -19.803, south: -19.968 },
  mobile: { width: 358, height: 256, west: -44.018, east: -43.895, north: -19.814, south: -19.955 },
};
const MARKER_LETTERS = { origin: "A", destination: "B", both: "A/B" };

/** Native pixel coordinates in the matching Figma SVG, before responsive scaling. */
export function projectStation(station, layout) {
  const bounds = MAP_LAYOUTS[layout];
  return {
    x: (station.longitude - bounds.west) / (bounds.east - bounds.west) * bounds.width,
    y: (bounds.north - station.latitude) / (bounds.north - bounds.south) * bounds.height,
  };
}

export function createStationMap(container, stations, onSelect, onClose) {
  const controls = stations.map(station => {
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
    detail.textContent = `Plataforma ${station.platform}`;
    label.append(name, detail);
    button.append(marker, label);
    return { station, button, point, letter, label, desktopName, mobileName };
  });
  container.replaceChildren(...controls.map(control => control.button));

  const layer = container.parentElement;
  const panel = layer.parentElement;
  const backdrop = document.querySelector("#map-backdrop");
  const expandedBar = document.querySelector("#map-expanded-bar");
  const originName = document.querySelector("#map-confirmed-origin");
  const closeButton = document.querySelector("#map-close");
  const pageRegions = [document.querySelector(".site-header"), document.querySelector(".search-panel")];
  let view = null;
  let expanded = false;

  function setPageInert(value) {
    pageRegions.forEach(region => {
      if (region) region.inert = value;
    });
  }

  function setExpanded(next, focusTarget = null) {
    if (expanded === next) return;
    const before = panel.getBoundingClientRect();
    expanded = next;
    if (next) panel.dataset.expanded = "true";
    else panel.removeAttribute("data-expanded");
    document.body.toggleAttribute("data-map-expanded", next);
    backdrop.hidden = !next;
    expandedBar.hidden = !next;
    panel.setAttribute("aria-modal", String(next));
    if (next) panel.setAttribute("role", "dialog");
    else {
      panel.removeAttribute("role");
      panel.removeAttribute("aria-modal");
    }
    setPageInert(next);
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduceMotion) animateMapLayout(panel, before, 620);
    if (next) closeButton.focus({ preventScroll: true });
    else if (focusTarget) focusTarget.focus({ preventScroll: true });
  }

  function collapse(focusTarget = null) {
    setExpanded(false, focusTarget);
  }

  function clearOriginConfirmation() {
    collapse();
    panel.removeAttribute("data-origin-confirmed");
    controls.forEach(control => control.button.removeAttribute("data-confirmed"));
  }

  function confirmOrigin(station) {
    const control = controls.find(item => item.station.stationId === station.stationId);
    if (!control) return;
    clearOriginConfirmation();
    panel.dataset.originConfirmed = "true";
    control.button.dataset.confirmed = "true";
    originName.textContent = station.label;
    setExpanded(true);
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion || typeof control.button.querySelector(".map-marker").animate !== "function") return;
    control.button.querySelector(".map-marker").animate([
      { transform: "translate(-50%, -50%) scale(0.65)", opacity: 0.5 },
      { transform: "translate(-50%, -50%) scale(1.45)", opacity: 1, offset: 0.55 },
      { transform: "translate(-50%, -50%) scale(1)", opacity: 1 },
    ], { duration: 900, easing: "cubic-bezier(0.16, 1, 0.3, 1)" });
  }

  function render() {
    if (!view) return;
    const { selection, activeField, result } = view;
    const layout = window.matchMedia("(width < 960px)").matches ? "mobile" : "desktop";
    const size = MAP_LAYOUTS[layout];
    const scale = layer.getBoundingClientRect().width / size.width;
    layer.querySelector(`.network-image--${layout}`).style.transform = `scale(${scale})`;
    const route = document.querySelector("#map-route");
    const pill = document.querySelector("#route-pill");
    route.setAttribute("viewBox", `0 0 ${size.width} ${size.height}`);
    route.toggleAttribute("hidden", !result);
    pill.hidden = !result;
    document.querySelector("#map-key-station").hidden = Boolean(result);
    document.querySelector("#map-key-route").hidden = !result;
    document.querySelector("#map-key-label").textContent = result ? `Linha ${result.routeShortName}` : "Paradas de ônibus";
    document.querySelector("#map-key-short").textContent = result ? `Linha ${result.routeShortName}` : "Paradas";
    let dense = false;
    if (result) {
      const positions = result.stops.map(station => projectStation(station, layout));
      const first = positions[0];
      const last = positions.at(-1);
      // Nearby vertices retain their real coordinates; their labels carry A/B.
      dense = Math.hypot(last.x - first.x, last.y - first.y) * scale < 44;
      pill.hidden = dense;
      route.querySelector(".route-direction").toggleAttribute("hidden", dense);
      const points = positions.map(point => `${point.x},${point.y}`).join(" ");
      route.querySelectorAll("polyline").forEach(line => line.setAttribute("points", points));
      const [origin, next] = positions;
      const x = origin.x + (next.x - origin.x) * 0.48;
      const y = origin.y + (next.y - origin.y) * 0.48;
      const angle = Math.atan2(next.y - origin.y, next.x - origin.x) * 180 / Math.PI;
      route.querySelector(".route-direction").setAttribute("transform", `translate(${x} ${y}) rotate(${angle})`);
      pill.style.left = `${x * 100 / size.width}%`;
      pill.style.top = `${y * 100 / size.height}%`;
    }
    container.dataset.dense = String(dense);
    for (const { station, button, point, letter, label, desktopName, mobileName } of controls) {
      const position = projectStation(station, layout);
      button.style.left = `${position.x * 100 / size.width}%`;
      button.style.top = `${position.y * 100 / size.height}%`;
      const isOrigin = station.stationId === selection.originId;
      const isDestination = station.stationId === selection.destinationId;
      const selected = isOrigin || isDestination;
      let role = "";
      if (isOrigin) role = "origin";
      if (isDestination) role = "destination";
      if (isOrigin && isDestination) role = "both";

      button.dataset.selection = role;
      button.dataset.onRoute = String(Boolean(result?.stops.some(stop => stop.stationId === station.stationId)));
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
    const panel = layer.parentElement.getBoundingClientRect();
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

  closeButton.addEventListener("click", () => {
    collapse();
    onClose?.();
  });
  backdrop.addEventListener("click", () => {
    collapse();
    onClose?.();
  });
  document.addEventListener("keydown", event => {
    if (expanded && event.key === "Escape") {
      event.preventDefault();
      collapse();
      onClose?.();
    }
  });

  new ResizeObserver(render).observe(layer.parentElement);
  return {
    update(selection, activeField, result = null) {
      view = { selection, activeField, result };
      render();
    },
    confirmOrigin,
    clearOriginConfirmation,
    collapse,
    get expanded() {
      return expanded;
    },
  };
}
