import { DEMO_STATIONS, DEMO_TRIP } from "./demo-data.js";
import { createStationMap } from "./map.js";
import {
  createSelection,
  editStation,
  searchStations,
  selectStation,
  validateSelection,
} from "./selection.js";

const form = document.querySelector("#route-form");
const departureInput = document.querySelector("#departure-time");
const submitButton = form.querySelector(".search-button");
const status = document.querySelector("#selection-status");
const mapRole = document.querySelector("#map-selection-role");
const touched = new Set();
const fields = Object.fromEntries(["origin", "destination"].map(field => [field, {
  wrapper: document.getElementById(`${field}-field`),
  input: document.getElementById(field),
  clear: document.getElementById(`${field}-clear`),
  icon: document.getElementById(`${field}-search-icon`),
  list: document.getElementById(`${field}-options`),
  empty: document.getElementById(`${field}-empty`),
  error: document.getElementById(`${field}-error`),
}]));

let selection = createSelection();
let activeField = "origin";
let openField = null;
let options = [];
let activeOption = -1;

const map = createStationMap(document.querySelector("#map-stations"), DEMO_STATIONS, station => {
  chooseStation(activeField, station);
});

function setStatus(message) {
  status.textContent = message;
  status.hidden = message.length === 0;
}

function showError(input, element, message) {
  element.textContent = message ?? "";
  element.hidden = !message;
  input.setAttribute("aria-invalid", String(Boolean(message)));
}

function renderSelection() {
  const result = validateSelection(selection);
  for (const [field, controls] of Object.entries(fields)) {
    const value = selection[`${field}Text`];
    if (controls.input.value !== value) controls.input.value = value;
    controls.clear.hidden = value.length === 0;
    controls.icon.hidden = value.length !== 0;
    showError(controls.input, controls.error, touched.has(field) ? result.errors[field] : null);
  }
  if (departureInput.value !== selection.departureTime) departureInput.value = selection.departureTime;
  showError(departureInput, document.querySelector("#departure-error"),
    touched.has("departureTime") ? result.errors.departureTime : null);
  submitButton.disabled = result.query === null;
  map.update(selection, activeField);
  mapRole.textContent = activeField === "origin" ? "Origem" : "Destino";

  if (result.query) setStatus(`Paradas selecionadas para o exemplo da linha ${DEMO_TRIP.routeShortName}. Confira o horário de saída.`);
  else if (selection.originId && !selection.destinationId) setStatus("Origem selecionada. Escolha o destino.");
  else if (selection.destinationId && !selection.originId) setStatus("Destino selecionado. Escolha a origem.");
  else setStatus("");
  return result;
}

function closeOptions() {
  for (const controls of Object.values(fields)) {
    controls.list.hidden = true;
    controls.empty.hidden = true;
    controls.input.setAttribute("aria-expanded", "false");
    controls.input.removeAttribute("aria-activedescendant");
  }
  openField = null;
  options = [];
  activeOption = -1;
}

function chooseStation(field, station, focusNext = false) {
  selection = selectStation(selection, field, station);
  touched.add(field);
  closeOptions();
  activeField = field;
  if (field === "origin" && !selection.destinationId) activeField = "destination";
  if (field === "destination" && !selection.originId) activeField = "origin";
  renderSelection();
  if (focusNext) fields[activeField].input.focus();
}

function openOptions(field) {
  closeOptions();
  openField = field;
  const controls = fields[field];
  options = searchStations(selection[`${field}Text`]);
  const items = options.map(station => {
    const option = document.createElement("li");
    option.id = `${field}-option-${station.stationId}`;
    option.className = "station-option";
    option.setAttribute("role", "option");
    option.setAttribute("aria-selected", "false");

    const copy = document.createElement("span");
    copy.className = "suggestion-copy";
    const title = document.createElement("span");
    title.className = "suggestion-title";
    title.textContent = station.mapName;
    const detail = document.createElement("span");
    detail.className = "suggestion-detail";
    detail.textContent = `Plataforma ${station.platform} · ${station.district}`;
    copy.append(title, detail);
    const arrow = document.createElement("img");
    arrow.src = "/assets/icons/arrow.svg";
    arrow.alt = "";
    arrow.width = 15.2625;
    arrow.height = 12.5125;
    option.append(copy, arrow);

    // Keep the input focused until the click chooses an option, including touch.
    option.addEventListener("pointerdown", event => event.preventDefault());
    option.addEventListener("click", () => chooseStation(field, station, true));
    return option;
  });
  controls.list.replaceChildren(...items);
  controls.list.hidden = options.length === 0;
  controls.empty.hidden = options.length !== 0;
  controls.input.setAttribute("aria-expanded", String(options.length > 0));
}

function highlightOption(index) {
  activeOption = index;
  const controls = fields[openField];
  const items = [...controls.list.children];
  items.forEach((item, position) => item.setAttribute("aria-selected", String(position === index)));
  controls.input.setAttribute("aria-activedescendant", items[index].id);
  items[index].scrollIntoView({ block: "nearest" });
}

function handleStationKey(event, field) {
  if (event.key === "Escape") {
    event.preventDefault();
    closeOptions();
  } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    if (openField !== field) openOptions(field);
    if (options.length === 0) return;
    const index = event.key === "ArrowDown"
      ? (activeOption + 1) % options.length
      : (activeOption <= 0 ? options.length - 1 : activeOption - 1);
    highlightOption(index);
  } else if (event.key === "Enter" && openField === field && options.length > 0) {
    event.preventDefault();
    if (activeOption >= 0) chooseStation(field, options[activeOption], true);
    else if (options.length === 1) chooseStation(field, options[0], true);
    else setStatus("Use as setas para escolher uma parada da lista.");
  }
}

for (const [field, controls] of Object.entries(fields)) {
  controls.input.addEventListener("focus", () => {
    activeField = field;
    renderSelection();
    openOptions(field);
  });
  controls.input.addEventListener("input", () => {
    selection = editStation(selection, field, controls.input.value);
    touched.delete(field);
    renderSelection();
    openOptions(field);
  });
  controls.input.addEventListener("keydown", event => handleStationKey(event, field));
  controls.input.addEventListener("blur", () => {
    touched.add(field);
    renderSelection();
  });
  controls.clear.addEventListener("click", () => {
    selection = editStation(selection, field, "");
    touched.delete(field);
    renderSelection();
    controls.input.focus();
    openOptions(field);
  });
}

for (const event of ["input", "blur"]) {
  departureInput.addEventListener(event, () => {
    selection = { ...selection, departureTime: departureInput.value };
    if (event === "blur") touched.add("departureTime");
    renderSelection();
  });
}

document.addEventListener("pointerdown", event => {
  if (openField && !fields[openField].wrapper.contains(event.target)) closeOptions();
});
document.addEventListener("focusin", event => {
  if (openField && !fields[openField].wrapper.contains(event.target)) closeOptions();
});

document.querySelector("#demo-trigger").addEventListener("click", () => {
  const firstId = DEMO_TRIP.stopTimes[0].stationId;
  const lastId = DEMO_TRIP.stopTimes.at(-1).stationId;
  const origin = DEMO_STATIONS.find(station => station.stationId === firstId);
  const destination = DEMO_STATIONS.find(station => station.stationId === lastId);
  selection = selectStation(createSelection(), "origin", origin);
  selection = selectStation(selection, "destination", destination);
  touched.clear();
  activeField = "destination";
  closeOptions();
  renderSelection();
});

form.addEventListener("submit", event => {
  event.preventDefault();
  closeOptions();
  ["origin", "destination", "departureTime"].forEach(field => touched.add(field));
  const result = renderSelection();
  if (!result.query) {
    if (result.errors.origin) fields.origin.input.focus();
    else if (result.errors.destination) fields.destination.input.focus();
    else departureInput.focus();
    return;
  }
  setStatus(`Consulta preparada: ${selection.originText} → ${selection.destinationText}. Saída ${result.query.departureTime}.`);
});

renderSelection();
