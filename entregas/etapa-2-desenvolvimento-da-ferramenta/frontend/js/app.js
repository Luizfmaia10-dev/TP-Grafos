import {
  getGeocodingConfig,
  listSnapCandidates,
  searchRoute,
  ApiError,
} from "./api-service.js";
import {
  createAddressSelection,
  selectOriginStation,
  setAddress,
  setSnapCandidates,
  setSnapUnavailable,
  setWalkLimit,
  validateAddressSelection,
} from "./address-selection.js";
import { createDialog } from "./dialog.js";
import { createAddressAutocomplete } from "./geoapify-autocomplete.js";
import { createStationMap, currentMapStations } from "./map.js";
import { createRouteRequest } from "./route-request.js";
import { formatDuration, renderRoute } from "./route-view.js";
import { describeWalkLimit, walkLimitProgress } from "./snap-controls.js";
import { maskDepartureTime } from "./time-mask.js";
import { createTimePicker } from "./time-picker.js";
import { createThemeSwitch } from "./theme.js";

const form = document.querySelector("#route-form");
const departureInput = document.querySelector("#departure-time");
const submitButton = form.querySelector(".search-button");
const status = document.querySelector("#selection-status");
const planner = document.querySelector("#planner");
const title = document.querySelector("#planner-title");
const description = document.querySelector("#planner-description");
const editSearch = document.querySelector("#edit-search");
const summary = document.querySelector("#route-summary");
const itinerary = document.querySelector("#route-itinerary");
const feedback = document.querySelector("#query-feedback");
const announcement = document.querySelector("#query-announcement");
const originElement = document.querySelector("#origin-dialog");
const limitsElement = document.querySelector("#limits-dialog");
const originDialog = createDialog(originElement);
const limitsDialog = createDialog(limitsElement);
const originTrigger = document.querySelector("#origin-dialog-trigger");
const originChange = document.querySelector("#origin-change");
const limitsTrigger = document.querySelector("#limits-dialog-trigger");
const destinationClear = document.querySelector("#destination-clear");
const originConfirm = document.querySelector("#origin-confirm");
const limitConfirm = document.querySelector("#limit-confirm");

createThemeSwitch(document.querySelector("#theme-switch"));
const timePicker = createTimePicker(
  document.querySelector("#departure-picker"),
  departureInput,
  document.querySelector("#departure-picker-trigger"),
);

let selection = createAddressSelection();
let originDraft = selection;
let limitDraft = selection;
let limitField = "origin";
let geocodingKey = null;
let originLoading = false;
let destinationLoading = false;
let limitLoading = false;
let originRequestError = null;
let destinationRequestError = null;
let limitRequestError = null;
let limitTimer = null;
const touched = new Set();
const snapControllers = new Map();

const request = createRouteRequest(searchRoute, renderRequest);
const map = createStationMap(document.querySelector("#map-stations"), () => {});

const ERROR_MESSAGES = {
  "unknown-station": ["Parada não encontrada", "Escolha novamente os endereços."],
  invalid: ["Dados inválidos", "Confira os endereços, limites e horário de saída."],
  unavailable: ["Rede indisponível", "O servidor ainda não carregou a rede de transporte."],
  "no-station": ["Nenhuma parada próxima", "Aumente o limite de caminhada ou escolha outro endereço."],
};

function announce(message) {
  if (announcement.textContent !== message) announcement.textContent = message;
}

function errorMessage(error) {
  if (error instanceof ApiError) {
    return ERROR_MESSAGES[error.kind]
      ?? ["Não foi possível consultar a rede", "O servidor não concluiu a consulta. Tente novamente."];
  }
  return ["Falha de conexão", "Não foi possível receber os dados. Verifique sua conexão e tente novamente."];
}

function selectedStation(field, state = selection) {
  const point = state[field];
  if (field === "origin") {
    return point.candidates.find(candidate => candidate.station.stationId === point.stationId)?.station ?? null;
  }
  return point.candidates[0]?.station ?? null;
}

function mapSelection(result = null) {
  if (result) {
    return {
      originId: result.origin.stationId,
      originText: result.origin.label,
      destinationId: result.destination.stationId,
      destinationText: result.destination.label,
    };
  }
  const origin = selectedStation("origin");
  const destination = selectedStation("destination");
  return {
    originId: origin?.stationId ?? null,
    originText: origin?.label ?? "",
    destinationId: destination?.stationId ?? null,
    destinationText: destination?.label ?? "",
  };
}

function refreshMap() {
  const result = request.state.status === "found" ? request.state : null;
  const adapter = mapSelection(result);
  const selected = result
    ? currentMapStations([], [], adapter, result)
    : [selectedStation("origin"), selectedStation("destination")].filter(Boolean);
  map.setStations(selected);
  map.update(adapter, null, result);
  const mapRole = document.querySelector("#map-selection-role");
  mapRole.hidden = Boolean(result);
  mapRole.textContent = "Pontos conectados";
  document.querySelector("#map-description").textContent = result
    ? `Trajeto de ${selection.origin.address.label} até ${selection.destination.address.label}. As linhas pontilhadas mostram as caminhadas até a rede.`
    : "Mapa esquemático da rede. As paradas conectadas aos endereços aparecem depois da confirmação.";
}

function setStatus(message) {
  status.textContent = message;
  status.hidden = message.length === 0;
}

function showFieldError(id, message, visible) {
  const element = document.querySelector(id);
  element.textContent = message ?? "";
  element.hidden = !message || !visible;
}

function renderSelection() {
  const validation = validateAddressSelection(selection);
  const originStation = selectedStation("origin");
  const destinationStation = selectedStation("destination");
  const originAddress = selection.origin.address;
  const destinationAddress = selection.destination.address;

  document.querySelector("#origin-address-label").textContent = originAddress?.label ?? "Origem ainda não definida";
  document.querySelector("#origin-station-label").textContent = originStation
    ? `${originStation.label} · ${selection.origin.candidates.find(item => item.station.stationId === originStation.stationId).distanceMeters} m a pé`
    : "Informe um endereço e confirme a parada de acesso.";
  originTrigger.querySelector("span:last-child").textContent = originAddress ? "Alterar origem" : "Definir origem";
  destinationClear.hidden = !destinationAddress;
  document.querySelector("#limits-trigger-label").textContent = `A ${selection.origin.maxWalkMeters} m · B ${selection.destination.maxWalkMeters} m`;

  if (!destinationLoading) {
    const destinationStatus = document.querySelector("#destination-snap-status");
    if (destinationRequestError) destinationStatus.textContent = destinationRequestError;
    else if (destinationStation) {
      const distance = selection.destination.candidates[0].distanceMeters;
      destinationStatus.textContent = `Parada conectada automaticamente: ${destinationStation.label} · ${distance} m a pé.`;
    } else if (destinationAddress) destinationStatus.textContent = "Nenhuma parada disponível dentro do limite escolhido.";
    else destinationStatus.textContent = "A parada mais próxima será escolhida automaticamente.";
  }

  showFieldError("#origin-error", validation.errors.origin, touched.has("origin"));
  showFieldError("#destination-error", validation.errors.destination, touched.has("destination"));
  showFieldError("#departure-error", validation.errors.departureTime, touched.has("departureTime"));

  const loading = request.state.status === "loading";
  submitButton.disabled = loading || validation.query === null;
  submitButton.dataset.loading = String(loading);
  submitButton.textContent = loading ? "Calculando trajeto…" : "Calcular trajeto";
  if (loading) setStatus("Consultando os horários da rede… Você pode editar os campos para cancelar.");
  else if (validation.query) setStatus("Endereços conectados à rede. Confira o horário de saída.");
  else if (originAddress && !destinationAddress) setStatus("Origem definida. Informe o endereço de destino.");
  else if (destinationAddress && !originAddress) setStatus("Destino definido. Agora defina a origem.");
  else setStatus("");
  refreshMap();
  return validation;
}

function renderRequest(state) {
  const found = state.status === "found";
  planner.dataset.view = found ? "result" : "search";
  title.textContent = found ? "Seu trajeto" : "Planeje seu trajeto";
  description.textContent = found
    ? `Dia de serviço: ${state.serviceDate}`
    : "Informe os endereços para conectá-los à rede de transporte.";
  form.hidden = found;
  editSearch.hidden = !found;
  summary.hidden = !found;
  itinerary.hidden = !found;
  form.setAttribute("aria-busy", String(state.status === "loading"));
  renderSelection();

  const messages = {
    "no-route": ["Nenhum trajeto encontrado", "Não há ligação disponível para este horário. Ajuste a busca."],
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
    document.querySelector("#itinerary-steps").replaceChildren();
    announce(state.status === "loading" ? "Calculando trajeto." : message?.join(" ") ?? "Busca pronta para edição.");
  }
}

function requestCandidates(state, field, requestKey, onChange, onBusy, onError) {
  snapControllers.get(requestKey)?.abort();
  const controller = new AbortController();
  snapControllers.set(requestKey, controller);
  onBusy(true);
  const point = state[field];
  return listSnapCandidates({
    ...point.address,
    maxWalkMeters: point.maxWalkMeters,
  }, { signal: controller.signal })
    .then(result => onChange(setSnapCandidates(state, field, result)))
    .catch(error => {
      if (controller.signal.aborted) return;
      if (error instanceof ApiError && error.kind === "no-station") {
        onChange(setSnapUnavailable(state, field, error.detail?.minimum_distance_meters ?? null));
      } else onError(errorMessage(error).join(" "));
    })
    .finally(() => {
      if (snapControllers.get(requestKey) === controller) {
        snapControllers.delete(requestKey);
        onBusy(false);
      }
    });
}

function renderOriginDialog() {
  const point = originDraft.origin;
  const visibleCandidates = point.candidates.slice(0, 20);
  const container = document.querySelector("#origin-candidates");
  document.querySelector("#origin-limit-chip").textContent = `Até ${point.maxWalkMeters} m`;
  const statusElement = document.querySelector("#origin-candidates-status");
  if (originLoading) statusElement.textContent = "Procurando paradas dentro do seu limite…";
  else if (originRequestError) statusElement.textContent = originRequestError;
  else if (!point.address) statusElement.textContent = "Informe um endereço para encontrar paradas próximas.";
  else if (point.candidates.length === 0) {
    statusElement.textContent = point.minimumDistanceMeters == null
      ? "Nenhuma parada foi encontrada em até 2 km desse endereço."
      : `Nenhuma parada dentro de ${point.maxWalkMeters} m. Distância mínima necessária: ${point.minimumDistanceMeters} m.`;
  } else statusElement.textContent = point.candidates.length > visibleCandidates.length
    ? `${point.candidates.length} paradas dentro do limite. Mostrando as 20 mais próximas.`
    : `${point.candidates.length} ${point.candidates.length === 1 ? "parada encontrada" : "paradas encontradas"}.`;

  container.replaceChildren(...visibleCandidates.map((candidate, index) => {
    const label = document.createElement("label");
    label.className = "candidate-card";
    label.dataset.selected = String(candidate.station.stationId === point.stationId);
    const input = document.createElement("input");
    input.type = "radio";
    input.name = "origin-station";
    input.value = candidate.station.stationId;
    input.checked = candidate.station.stationId === point.stationId;
    input.addEventListener("change", () => {
      originDraft = selectOriginStation(originDraft, input.value);
      renderOriginDialog();
    });
    const copy = document.createElement("span");
    copy.className = "candidate-copy";
    const name = document.createElement("strong");
    name.textContent = candidate.station.label;
    const detail = document.createElement("span");
    detail.textContent = `${candidate.distanceMeters} m a pé${index === 0 ? " · Mais próxima" : ""}`;
    copy.append(name, detail);
    const mark = document.createElement("span");
    mark.className = "candidate-radio";
    mark.setAttribute("aria-hidden", "true");
    label.append(input, copy, mark);
    return label;
  }));
  originConfirm.disabled = originLoading || !point.address || !point.stationId;
}

function loadOriginCandidates() {
  originRequestError = null;
  renderOriginDialog();
  requestCandidates(
    originDraft,
    "origin",
    "origin-dialog",
    next => { originDraft = next; renderOriginDialog(); },
    busy => { originLoading = busy; renderOriginDialog(); },
    message => { originRequestError = message; renderOriginDialog(); },
  );
}

function mountOriginAutocomplete() {
  if (!geocodingKey) return;
  createAddressAutocomplete(
    geocodingKey,
    document.querySelector("#origin-autocomplete"),
    address => {
      originDraft = setAddress(originDraft, "origin", address);
      originRequestError = null;
      document.querySelector("#origin-address-error").hidden = true;
      loadOriginCandidates();
    },
    message => {
      const error = document.querySelector("#origin-address-error");
      error.textContent = message;
      error.hidden = false;
    },
  );
}

function openOrigin(trigger) {
  if (!geocodingKey) return;
  originDraft = selection;
  originRequestError = null;
  mountOriginAutocomplete();
  renderOriginDialog();
  originDialog.open(trigger);
}

function renderDestination() {
  const element = document.querySelector("#destination-snap-status");
  if (destinationLoading) element.textContent = "Procurando a parada mais próxima…";
  renderSelection();
}

function loadDestinationCandidates() {
  destinationRequestError = null;
  renderDestination();
  requestCandidates(
    selection,
    "destination",
    "destination",
    next => { selection = next; renderDestination(); },
    busy => { destinationLoading = busy; renderDestination(); },
    message => { destinationRequestError = message; renderDestination(); },
  );
}

function mountDestinationAutocomplete() {
  const container = document.querySelector("#destination-autocomplete");
  if (!geocodingKey) return;
  createAddressAutocomplete(
    geocodingKey,
    container,
    address => {
      selection = setAddress(selection, "destination", address);
      request.cancel();
      touched.delete("destination");
      loadDestinationCandidates();
    },
    message => {
      destinationRequestError = message;
      renderDestination();
    },
  );
}

function renderLimitDialog() {
  const point = limitDraft[limitField];
  const fieldLabel = limitField === "origin" ? "origem" : "destino";
  document.querySelectorAll("[data-limit-field]").forEach(tab => {
    tab.setAttribute("aria-selected", String(tab.dataset.limitField === limitField));
  });
  document.querySelector("#limit-visual-point").textContent = limitField === "origin" ? "A" : "B";
  const progress = walkLimitProgress(point.maxWalkMeters);
  document.querySelector("#limit-visual").style.setProperty(
    "--walk-scale",
    String(0.45 + (progress * 0.55)),
  );
  document.querySelector("#limit-slider").value = String(point.maxWalkMeters);
  document.querySelector("#limit-value").textContent = point.maxWalkMeters >= 1_000
    ? `${(point.maxWalkMeters / 1_000).toLocaleString("pt-BR")} km`
    : `${point.maxWalkMeters} m`;
  document.querySelectorAll("[data-limit-value]").forEach(button => {
    button.dataset.selected = String(Number(button.dataset.limitValue) === point.maxWalkMeters);
  });
  const address = document.querySelector("#limit-address");
  address.textContent = point.address?.label ?? `Endereço de ${fieldLabel} ainda não informado.`;
  const feedbackElement = document.querySelector("#limit-feedback");
  const message = document.querySelector("#limit-message");
  if (limitLoading) {
    feedbackElement.dataset.state = "loading";
    message.textContent = "Verificando as paradas disponíveis para este limite…";
    limitConfirm.disabled = true;
  } else if (limitRequestError) {
    feedbackElement.dataset.state = "error";
    message.textContent = limitRequestError;
    limitConfirm.disabled = true;
  } else {
    const limitDescription = describeWalkLimit(point, limitField);
    feedbackElement.dataset.state = limitDescription.state;
    message.textContent = limitDescription.message;
    limitConfirm.disabled = !limitDescription.canConfirm;
  }
}

function prepareLimit(field) {
  snapControllers.get("limit")?.abort();
  clearTimeout(limitTimer);
  limitField = field;
  limitDraft = selection;
  limitRequestError = null;
  limitLoading = false;
  renderLimitDialog();
}

function verifyLimit() {
  const point = limitDraft[limitField];
  if (!point.address) {
    renderLimitDialog();
    return;
  }
  limitRequestError = null;
  const previousOriginId = selection.origin.stationId;
  requestCandidates(
    limitDraft,
    limitField,
    "limit",
    next => {
      if (limitField === "origin" && previousOriginId
          && next.origin.candidates.some(item => item.station.stationId === previousOriginId)) {
        next = selectOriginStation(next, previousOriginId);
      }
      limitDraft = next;
      renderLimitDialog();
    },
    busy => { limitLoading = busy; renderLimitDialog(); },
    message => { limitRequestError = message; renderLimitDialog(); },
  );
}

function updatePendingLimit(value) {
  limitDraft = setWalkLimit(selection, limitField, value);
  limitRequestError = null;
  renderLimitDialog();
  clearTimeout(limitTimer);
  limitTimer = setTimeout(verifyLimit, 220);
}

originTrigger.addEventListener("click", () => openOrigin(originTrigger));
originChange.addEventListener("click", () => openOrigin(originChange));
limitsTrigger.addEventListener("click", () => {
  prepareLimit("origin");
  limitsDialog.open(limitsTrigger);
});

document.querySelectorAll("[data-dialog-close]").forEach(button => {
  button.addEventListener("click", () => {
    const dialog = button.dataset.dialogClose === "origin-dialog" ? originDialog : limitsDialog;
    dialog.close();
  });
});

originElement.addEventListener("close", () => snapControllers.get("origin-dialog")?.abort());
limitsElement.addEventListener("close", () => {
  snapControllers.get("limit")?.abort();
  clearTimeout(limitTimer);
});

originConfirm.addEventListener("click", () => {
  if (!originDraft.origin.address || !originDraft.origin.stationId) return;
  selection = originDraft;
  request.cancel();
  touched.delete("origin");
  originDialog.close();
  renderSelection();
  announce(`Origem definida: ${selection.origin.address.label}.`);
});

destinationClear.addEventListener("click", () => {
  snapControllers.get("destination")?.abort();
  selection = setAddress(selection, "destination", null);
  destinationRequestError = null;
  touched.delete("destination");
  request.cancel();
  mountDestinationAutocomplete();
  renderSelection();
  announce("Destino limpo. Informe outro endereço.");
});

document.querySelectorAll("[data-limit-field]").forEach(tab => {
  tab.addEventListener("click", () => prepareLimit(tab.dataset.limitField));
});
document.querySelector("#limit-slider").addEventListener("input", event => {
  updatePendingLimit(Number(event.target.value));
});
document.querySelectorAll("[data-limit-value]").forEach(button => {
  button.addEventListener("click", () => updatePendingLimit(Number(button.dataset.limitValue)));
});
limitConfirm.addEventListener("click", () => {
  if (limitConfirm.disabled) return;
  selection = limitDraft;
  request.cancel();
  limitsDialog.close();
  renderSelection();
  announce(`Limite de ${limitField === "origin" ? "origem" : "destino"} atualizado para ${selection[limitField].maxWalkMeters} metros.`);
});

for (const event of ["input", "blur"]) {
  departureInput.addEventListener(event, () => {
    if (event === "input") departureInput.value = maskDepartureTime(departureInput.value);
    selection = { ...selection, departureTime: departureInput.value };
    if (event === "input") request.cancel();
    if (event === "blur" && selection.departureTime) touched.add("departureTime");
    renderSelection();
  });
}

form.addEventListener("submit", event => {
  event.preventDefault();
  if (request.state.status === "loading") return;
  timePicker.close({ restoreFocus: false });
  ["origin", "destination", "departureTime"].forEach(field => touched.add(field));
  const validation = renderSelection();
  if (!validation.query) {
    announce(Object.values(validation.errors).join(" "));
    if (validation.errors.origin) openOrigin(originChange);
    else if (validation.errors.destination) document.querySelector("#destination-autocomplete input")?.focus();
    else departureInput.focus();
    return;
  }
  request.submit(validation.query);
});

editSearch.addEventListener("click", () => {
  request.cancel();
  openOrigin(editSearch);
});

async function initializeGeocoding() {
  try {
    const config = await getGeocodingConfig();
    if (!config.available || !config.apiKey) throw new Error("Geocoding configuration is unavailable");
    geocodingKey = config.apiKey;
    mountDestinationAutocomplete();
  } catch {
    const message = "Busca de endereços indisponível. Configure o Geoapify para continuar.";
    originTrigger.disabled = true;
    originChange.disabled = true;
    const destination = document.querySelector("#destination-autocomplete");
    destination.textContent = message;
    destination.dataset.unavailable = "true";
    announce(message);
  }
  renderSelection();
}

renderSelection();
initializeGeocoding();
