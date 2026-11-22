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
  const match = value.match(/^([0-9]{2,}):([0-5][0-9])$/u);
  if (!match || match[0] !== value) return null;
  return value;
}

export function validateSelection(selection) {
  const errors = {};
  const origin = selection.originId != null && selection.originText.trim()
    ? { stationId: selection.originId }
    : null;
  const destination = selection.destinationId != null && selection.destinationText.trim()
    ? { stationId: selection.destinationId }
    : null;
  const departureTime = normalizeDepartureTime(selection.departureTime);

  if (!origin) errors.origin = "Escolha uma parada da lista ou do mapa.";
  if (!destination) errors.destination = "Escolha uma parada da lista ou do mapa.";
  if (origin && destination && origin.stationId === destination.stationId) {
    errors.destination = "Origem e destino precisam ser paradas diferentes.";
  }
  if (departureTime === null) {
    errors.departureTime = "Use HH:MM, sem segundos, com minutos entre 00 e 59.";
  }

  const query = Object.keys(errors).length === 0
    ? { originId: origin.stationId, destinationId: destination.stationId, departureTime }
    : null;
  return { errors, query };
}
