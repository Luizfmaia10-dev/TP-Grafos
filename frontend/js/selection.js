import { DEMO_STATIONS } from "./demo-data.js";

export function createSelection() {
  return {
    originId: null,
    originText: "",
    destinationId: null,
    destinationText: "",
    departureTime: "07:45",
  };
}

export function selectStation(selection, field, station) {
  return {
    ...selection,
    [`${field}Id`]: station.stationId,
    [`${field}Text`]: station.label,
  };
}

/** Every edit invalidates the previous ID, even when the label looks identical. */
export function editStation(selection, field, text) {
  return { ...selection, [`${field}Id`]: null, [`${field}Text`]: text };
}

export function normalizeDepartureTime(value) {
  const match = value.match(/^([0-9]{2,}):([0-5][0-9])(?::([0-5][0-9]))?$/u);
  if (!match || match[0] !== value) return null;
  return `${match[1]}:${match[2]}:${match[3] ?? "00"}`;
}

export function validateSelection(selection) {
  const errors = {};
  const origin = DEMO_STATIONS.find(station =>
    station.stationId === selection.originId && station.label === selection.originText);
  const destination = DEMO_STATIONS.find(station =>
    station.stationId === selection.destinationId && station.label === selection.destinationText);
  const departureTime = normalizeDepartureTime(selection.departureTime);

  if (!origin) errors.origin = "Escolha uma parada da lista ou do mapa.";
  if (!destination) errors.destination = "Escolha uma parada da lista ou do mapa.";
  if (origin && destination && origin.stationId === destination.stationId) {
    errors.destination = "Origem e destino precisam ser paradas diferentes.";
  }
  if (departureTime === null) {
    errors.departureTime = "Use HH:MM ou HH:MM:SS, com minutos e segundos entre 00 e 59.";
  }

  const query = Object.keys(errors).length === 0
    ? { originId: origin.stationId, destinationId: destination.stationId, departureTime }
    : null;
  return { errors, query };
}

function normalizeSearch(value) {
  return value.normalize("NFD").replace(/\p{M}/gu, "").toLocaleLowerCase("pt-BR").trim();
}

export function searchStations(text) {
  const query = normalizeSearch(text);
  return DEMO_STATIONS.filter(station => {
    const searchableText = `${station.name} ${station.label} ${station.shortName}`;
    return normalizeSearch(searchableText).includes(query);
  });
}
