import { listStations, searchRoute, ApiError } from "./api-service.js";
import { createStationRequest } from "./station-request.js";
import { createFieldActivity, shouldCloseStationOptions } from "./field-activity.js";
import { createStationMap, currentMapStations } from "./map.js";
import { createRouteRequest } from "./route-request.js";
import { formatDuration, renderRoute } from "./route-view.js";
import { maskDepartureTime } from "./time-mask.js";
import { createTimePicker } from "./time-picker.js";
import { createThemeSwitch } from "./theme.js";
import {
  createSelection,
  editStation,
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
  loading: document.getElementById(`${field}-loading`),
  error: document.getElementById(`${field}-error`),
}]));

let selection = createSelection();
const fieldActivity = createFieldActivity();
let openField = null;
let options = [];
let activeOption = -1;
let knownStations = [];

const map = createStationMap(
  document.querySelector("#map-stations"),
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
const request = createRouteRequest(searchRoute, renderRequest);
const stationRequests = Object.fromEntries(Object.keys(fields).map(field => [
  field, createStationRequest(listStations, state => renderOptions(field, state)),
]));
const ERROR_MESSAGES = {
  "unknown-station": ["Parada não encontrada", "Escolha novamente a origem e o destino."],
  invalid: ["Dados inválidos", "Confira as paradas e o horário de saída."],
  unavailable: ["Rede indisponível", "O servidor ainda não carregou a rede de transporte."],
};

function errorMessage(error) {
  if (error instanceof ApiError) {
    return ERROR_MESSAGES[error.kind] ?? ["Não foi possível consultar a rede", "O servidor não concluiu a consulta. Tente novamente."];
  }
  return ["Falha de conexão", "Não foi possível receber os dados. Verifique sua conexão e tente novamente."];
}

function refreshMapStations() {
  knownStations = currentMapStations(knownStations, options, selection,
    request.state.status === "found" ? request.state : null);
  map.setStations(knownStations);
}

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
  description.textContent = found ? `Dia de serviço: ${state.serviceDate}` : "Escolha duas paradas pelo nome ou no mapa.";
  form.hidden = found;
  editSearch.hidden = !found;
  summary.hidden = !found;
  itinerary.hidden = !found;
  form.setAttribute("aria-busy", String(loading));
  submitButton.dataset.loading = String(loading);
  submitButton.textContent = loading ? "Calculando trajeto…" : "Calcular trajeto";
  renderSelection();

  const messages = {
    "no-route": ["Nenhum trajeto encontrado", "Não há ligação disponível para essas paradas e esse horário no dia de serviço. Ajuste a busca."],
    error: errorMessage(state.error),
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
    announce(`Trajeto encontrado. Total: ${formatDuration(state.totalSeconds)}. Chegada às ${state.arrivalTime}.`);
    title.focus({ preventScroll: true });
    window.scrollTo({ top: 0 });
  } else {
    announce(loading ? "Calculando trajeto. Edite os campos para cancelar." : message ? message.join(" ") : "Busca pronta para edição.");
    document.querySelector("#itinerary-steps").replaceChildren();
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
  refreshMapStations();
  map.update(selection, activeField, found ? request.state : null);
  mapRole.hidden = found;
  mapRole.textContent = activeField === "origin" ? "Origem" : activeField === "destination" ? "Destino" : "Escolha um campo";
  document.querySelector("#map-description").textContent = found
    ? `Trajeto de ${selection.originText} até ${selection.destinationText}. Os trechos são identificados por modal na legenda. A marca a origem e B marca o destino.`
    : "Mapa esquemático da rede de transporte de Belo Horizonte. Busque paradas pelo nome para exibi-las no mapa. Os marcadores A e B identificam suas escolhas.";

  if (loading) setStatus("Consultando os horários da rede… Você pode editar os campos para cancelar.");
  else if (result.query) setStatus("Paradas selecionadas. Confira o horário de saída.");
  else if (selection.originId && !selection.destinationId) setStatus("Origem selecionada. Escolha o destino.");
  else if (selection.destinationId && !selection.originId) setStatus("Destino selecionado. Escolha a origem.");
  else setStatus("");
  return result;
}

function closeOptions() {
  openField = null;
  options = [];
  for (const stationRequest of Object.values(stationRequests)) stationRequest.cancel();
  for (const controls of Object.values(fields)) {
    controls.list.hidden = true;
    controls.empty.hidden = true;
    controls.loading.hidden = true;
    controls.input.closest(".station-picker").setAttribute("aria-busy", "false");
    controls.input.setAttribute("aria-expanded", "false");
    controls.input.removeAttribute("aria-activedescendant");
  }
  activeOption = -1;
  refreshMapStations();
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
  stationRequests[field].submit(selection[`${field}Text`]);
}

function renderOptions(field, state) {
  if (openField !== field) return;
  const controls = fields[field];
  const loading = state.status === "loading";
  controls.input.closest(".station-picker").setAttribute("aria-busy", String(loading));
  controls.loading.hidden = !loading;
  options = state.status === "ready" ? state.stations : [];
  activeOption = -1;
  controls.input.removeAttribute("aria-activedescendant");
  refreshMapStations();
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
    detail.textContent = `Parada ${station.stationId}`;
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
  controls.empty.hidden = !["empty", "error"].includes(state.status);
  controls.empty.textContent = state.status === "error"
    ? errorMessage(state.error).join(". ") : "Nenhuma parada encontrada na rede para esta busca.";
  controls.input.setAttribute("aria-expanded", String(options.length > 0));
  const fieldName = field === "origin" ? "origem" : "destino";
  if (!loading) announce(options.length ? `${options.length} ${options.length === 1 ? "parada encontrada" : "paradas encontradas"} para ${fieldName}. Use as setas e Enter para selecionar.`
    : controls.empty.hidden ? "" : controls.empty.textContent);
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
  if (openField && shouldCloseStationOptions(fields[openField].wrapper, event.target)) closeOptions();
});
document.addEventListener("focusin", event => {
  if (openField && shouldCloseStationOptions(fields[openField].wrapper, event.target)) closeOptions();
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
