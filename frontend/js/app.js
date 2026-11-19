import { DEMO_STATIONS, DEMO_TRIP } from "./demo-data.js";
import { createFieldActivity } from "./field-activity.js";
import { createStationMap } from "./map.js";
import { searchDemoRoute } from "./demo-service.js";
import { createRouteRequest } from "./route-request.js";
import { formatDuration, renderRoute } from "./route-view.js";
import { maskDepartureTime } from "./time-mask.js";
import { createTimePicker } from "./time-picker.js";
import { createThemeSwitch } from "./theme.js";
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
const planner = document.querySelector("#planner");
const title = document.querySelector("#planner-title");
const description = document.querySelector("#planner-description");
const demoTrigger = document.querySelector("#demo-trigger");
const editSearch = document.querySelector("#edit-search");
const summary = document.querySelector("#route-summary");
const itinerary = document.querySelector("#route-itinerary");
const feedback = document.querySelector("#query-feedback");
const announcement = document.querySelector("#query-announcement");
createThemeSwitch(document.querySelector("#theme-switch"));
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
const fieldActivity = createFieldActivity();
let openField = null;
let options = [];
let activeOption = -1;

const map = createStationMap(
  document.querySelector("#map-stations"),
  DEMO_STATIONS,
  station => {
    const field = fieldActivity.activeField;
    if (!field) return;
    chooseStation(field, station);
  },
);
const timePicker = createTimePicker(
  document.querySelector("#departure-picker"),
  departureInput,
  document.querySelector("#departure-picker-trigger"),
);
const request = createRouteRequest(searchDemoRoute, renderRequest);

function editStationField(field) {
  fields[field].input.focus();
}

function announce(message) {
  if (announcement.textContent !== message) announcement.textContent = message;
}

function renderRequest(state) {
  const loading = state.status === "loading";
  const found = state.status === "found";
  planner.dataset.view = found ? "result" : "search";
  title.textContent = found ? "Seu trajeto" : "Planeje seu trajeto";
  description.textContent = found ? `Trajeto de exemplo · linha ${state.routeShortName}` : "Escolha duas paradas pelo nome ou no mapa.";
  form.hidden = found;
  demoTrigger.hidden = found;
  document.querySelector("#demo-scope").hidden = found;
  editSearch.hidden = !found;
  summary.hidden = !found;
  itinerary.hidden = !found;
  form.setAttribute("aria-busy", String(loading));
  submitButton.dataset.loading = String(loading);
  submitButton.textContent = loading ? "Consultando exemplo…" : "Calcular trajeto";
  renderSelection();

  const messages = {
    "no-route": ["Sem partida neste horário", `A viagem do exemplo parte desta parada às ${state.boardingTime}. Escolha uma saída até esse horário ou use “Experimente a linha 50”.`],
    "outside-sample": ["Trecho fora do exemplo", "Esta amostra cobre três paradas no sentido Pampulha → Centro. A viagem de volta e outras paradas ficam fora deste exemplo."],
    error: ["Não foi possível consultar o exemplo", "Tente novamente. Suas paradas e o horário foram mantidos."],
  };
  const message = messages[state.status];
  feedback.hidden = !message;
  if (message) {
    document.querySelector("#feedback-title").textContent = message[0];
    document.querySelector("#feedback-description").textContent = message[1];
  }
  if (found) {
    timePicker.close({ restoreFocus: false });
    renderRoute(state);
    announce(`Trajeto de exemplo encontrado. Total: ${formatDuration(state.totalSeconds)}. Chegada às ${state.arrivalTime}.`);
    title.focus({ preventScroll: true });
    window.scrollTo({ top: 0 });
  } else {
    announce(loading ? "Consultando a viagem de exemplo da linha 50." : message ? message.join(". ") : "");
    if (!loading) document.querySelector("#itinerary-steps").replaceChildren();
  }
}

function setStatus(message) {
  status.textContent = message;
  status.hidden = message.length === 0;
}

function showError(input, element, message, touchedField, hasText) {
  const visible = Boolean(message && touchedField);
  element.textContent = message ?? "";
  // Reserve the draft error's space while typing so blur cannot move a click target.
  element.hidden = !message || (!visible && !hasText);
  element.style.visibility = visible ? "visible" : "hidden";
  element.setAttribute("aria-hidden", String(!visible));
  input.setAttribute("aria-invalid", String(visible));
  const hint = input.id === "departure-time" ? "departure-hint" : "station-hint";
  input.setAttribute("aria-describedby", `${hint}${visible ? ` ${element.id}` : ""}`);
}

function renderSelection() {
  const result = validateSelection(selection);
  for (const [field, controls] of Object.entries(fields)) {
    const value = selection[`${field}Text`];
    if (controls.input.value !== value) controls.input.value = value;
    controls.clear.hidden = value.length === 0;
    controls.icon.hidden = value.length !== 0;
    showError(controls.input, controls.error, result.errors[field], touched.has(field), value.length > 0);
  }
  if (departureInput.value !== selection.departureTime) departureInput.value = selection.departureTime;
  showError(departureInput, document.querySelector("#departure-error"),
    result.errors.departureTime, touched.has("departureTime"), selection.departureTime.length > 0);
  const loading = request.state.status === "loading";
  const found = request.state.status === "found";
  submitButton.disabled = loading || result.query === null;
  const activeField = fieldActivity.activeField;
  map.update(selection, activeField, found ? request.state : null);
  mapRole.hidden = found;
  mapRole.textContent = activeField === "origin" ? "Origem" : activeField === "destination" ? "Destino" : "Escolha um campo";
  document.querySelector("#map-description").textContent = found
    ? `Trajeto de exemplo da linha ${request.state.routeShortName}, de ${selection.originText} até ${selection.destinationText}. O traço vermelho liga as paradas no mapa esquemático. A marca a origem e B marca o destino.`
    : "Mapa esquemático da rede de ônibus de Belo Horizonte. Selecione as paradas do exemplo da linha 50 para preencher origem e destino. Os marcadores A e B identificam suas escolhas.";

  if (loading) setStatus("Consultando os horários da viagem de exemplo… Você pode editar os campos para cancelar.");
  else if (result.query) setStatus(`Paradas selecionadas para o exemplo da linha ${DEMO_TRIP.routeShortName}. Confira o horário de saída.`);
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
  request.cancel();
  touched.add(field);
  closeOptions();
  fieldActivity.activate(field);
  if (field === "origin" && !selection.destinationId) fieldActivity.activate("destination");
  if (field === "destination" && !selection.originId) fieldActivity.activate("origin");
  const result = renderSelection();
  announce(selection.originId && selection.destinationId && !result.query
    ? Object.values(result.errors).join(" ")
    : `${field === "origin" ? "Origem selecionada" : "Destino selecionado"}: ${station.label}.`);
  if (focusNext) {
    if (!selection.originId) fields.origin.input.focus();
    else if (!selection.destinationId) fields.destination.input.focus();
    else departureInput.focus();
  }
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
  const fieldName = field === "origin" ? "origem" : "destino";
  announce(options.length ? `${options.length} ${options.length === 1 ? "parada encontrada" : "paradas encontradas"} para ${fieldName}. Use as setas e Enter para selecionar.`
    : `Nenhuma parada do exemplo encontrada para ${fieldName}.`);
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
    fieldActivity.activate(field);
    renderSelection();
    openOptions(field);
  });
  controls.input.addEventListener("input", () => {
    selection = editStation(selection, field, controls.input.value);
    request.cancel();
    touched.delete(field);
    renderSelection();
    openOptions(field);
  });
  controls.input.addEventListener("keydown", event => handleStationKey(event, field));
  controls.input.addEventListener("blur", () => {
    if (selection[`${field}Text`]) touched.add(field);
    const result = renderSelection();
    if (selection[`${field}Text`] && result.errors[field]) announce(result.errors[field]);
  });
  controls.clear.addEventListener("click", () => {
    closeOptions();
    selection = editStation(selection, field, "");
    request.cancel();
    touched.delete(field);
    fieldActivity.deactivate();
    renderSelection();
    form.focus({ preventScroll: true });
    announce(`${field === "origin" ? "Origem limpa" : "Destino limpo"}. Escolha uma parada.`);
  });
  controls.input.addEventListener("pointerdown", () => {
    if (document.activeElement === controls.input && openField !== field) openOptions(field);
  });
}

for (const event of ["input", "blur"]) {
  departureInput.addEventListener(event, () => {
    if (event === "input") departureInput.value = maskDepartureTime(departureInput.value);
    selection = { ...selection, departureTime: departureInput.value };
    if (event === "input") request.cancel();
    if (event === "blur" && selection.departureTime) touched.add("departureTime");
    const result = renderSelection();
    if (event === "blur" && result.errors.departureTime) announce(result.errors.departureTime);
  });
}

document.addEventListener("pointerdown", event => {
  if (openField && !fields[openField].wrapper.contains(event.target)) closeOptions();
});
document.addEventListener("focusin", event => {
  if (openField && !fields[openField].wrapper.contains(event.target)) closeOptions();
});

demoTrigger.addEventListener("click", () => {
  request.cancel();
  const firstId = DEMO_TRIP.stopTimes[0].stationId;
  const lastId = DEMO_TRIP.stopTimes.at(-1).stationId;
  const origin = DEMO_STATIONS.find(station => station.stationId === firstId);
  const destination = DEMO_STATIONS.find(station => station.stationId === lastId);
  selection = selectStation(createSelection(), "origin", origin);
  selection = selectStation(selection, "destination", destination);
  touched.clear();
  fieldActivity.activate("destination");
  closeOptions();
  renderSelection();
  announce("Exemplo da linha 50 preenchido: Pampulha para Av. Paraná, 162, com saída às 07:45. Você pode calcular o trajeto.");
});

form.addEventListener("submit", event => {
  event.preventDefault();
  if (request.state.status === "loading") return;
  closeOptions();
  timePicker.close({ restoreFocus: false });
  ["origin", "destination", "departureTime"].forEach(field => touched.add(field));
  const result = renderSelection();
  if (!result.query) {
    announce(Object.values(result.errors).join(" "));
    if (result.errors.origin) editStationField("origin");
    else if (result.errors.destination) editStationField("destination");
    else departureInput.focus();
    return;
  }
  request.submit(result.query);
});

editSearch.addEventListener("click", () => {
  request.cancel();
  editStationField("origin");
});

renderSelection();
