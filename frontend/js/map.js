const MAP_BOUNDS = { west: -44.045, east: -43.861, north: -19.803, south: -19.968 };
const MAP_SIZE = { width: 960, height: 780 };
const MARKER_LETTERS = { origin: "A", destination: "B", both: "A/B" };

/** Project onto the coordinate bounds used by the exported 960 x 780 SVG. */
function stationPosition(station) {
  return {
    x: (station.longitude - MAP_BOUNDS.west) / (MAP_BOUNDS.east - MAP_BOUNDS.west) * 100,
    y: (MAP_BOUNDS.north - station.latitude) / (MAP_BOUNDS.north - MAP_BOUNDS.south) * 100,
  };
}

export function createStationMap(container, stations, onSelect) {
  const controls = stations.map(station => {
    const position = stationPosition(station);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "map-station";
    button.dataset.stationId = station.stationId;
    button.style.left = `${position.x}%`;
    button.style.top = `${position.y}%`;
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
    return { station, button, point, letter, desktopName, mobileName };
  });
  container.replaceChildren(...controls.map(control => control.button));

  return {
    update(selection, activeField, result = null) {
      const route = document.querySelector("#map-route");
      const pill = document.querySelector("#route-pill");
      route.toggleAttribute("hidden", !result);
      pill.hidden = !result;
      document.querySelector("#map-key-station").hidden = Boolean(result);
      document.querySelector("#map-key-route").hidden = !result;
      document.querySelector("#map-key-label").textContent = result ? `Linha ${result.routeShortName}` : "Paradas de ônibus";
      let dense = false;
      if (result) {
        const positions = result.stops.map(station => {
          const position = stationPosition(station);
          return { x: position.x * MAP_SIZE.width / 100, y: position.y * MAP_SIZE.height / 100 };
        });
        const first = positions[0];
        const last = positions.at(-1);
        // Nearby vertices retain their real coordinates; their labels carry A/B.
        dense = Math.hypot(last.x - first.x, last.y - first.y) < 44;
        pill.hidden = dense;
        route.querySelector(".route-direction").toggleAttribute("hidden", dense);
        const points = positions.map(point => `${point.x},${point.y}`).join(" ");
        route.querySelectorAll("polyline").forEach(line => line.setAttribute("points", points));
        const [origin, next] = positions;
        const x = origin.x + (next.x - origin.x) * 0.48;
        const y = origin.y + (next.y - origin.y) * 0.48;
        const angle = Math.atan2(next.y - origin.y, next.x - origin.x) * 180 / Math.PI;
        route.querySelector(".route-direction").setAttribute("transform", `translate(${x} ${y}) rotate(${angle})`);
        pill.style.left = `${x * 100 / MAP_SIZE.width}%`;
        pill.style.top = `${y * 100 / MAP_SIZE.height}%`;
      }
      container.dataset.dense = String(dense);
      for (const { station, button, point, letter, desktopName, mobileName } of controls) {
        const isOrigin = station.stationId === selection.originId;
        const isDestination = station.stationId === selection.destinationId;
        const selected = isOrigin || isDestination;
        let role = "";
        if (isOrigin) role = "origin";
        if (isDestination) role = "destination";
        if (isOrigin && isDestination) role = "both";

        button.dataset.selection = role;
        button.dataset.onRoute = String(Boolean(result?.stops.some(stop => stop.stationId === station.stationId)));
        button.disabled = Boolean(result);
        button.setAttribute("aria-pressed", String(selected));
        button.setAttribute("aria-label", result
          ? `${station.label}${isOrigin ? ", origem" : isDestination ? ", destino" : ""}`
          : `Selecionar ${station.label} como ${activeField === "origin" ? "origem" : "destino"}`);
        point.hidden = selected || Boolean(result);
        letter.hidden = !selected;
        letter.textContent = MARKER_LETTERS[role] ?? "";
        const prefix = dense && selected ? `${MARKER_LETTERS[role]} · ` : "";
        desktopName.textContent = prefix + station.mapName;
        mobileName.textContent = prefix + station.shortName;
      }
    },
  };
}
