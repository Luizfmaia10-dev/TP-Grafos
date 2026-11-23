import { normalizeDepartureTime } from "./selection.js";

const DEFAULT_WALK_METERS = 800;

function emptyPoint() {
  return {
    address: null,
    maxWalkMeters: DEFAULT_WALK_METERS,
    candidates: [],
    minimumDistanceMeters: null,
    stationId: null,
  };
}

export function createAddressSelection() {
  return {
    origin: emptyPoint(),
    destination: emptyPoint(),
    departureTime: "07:45",
  };
}

export function setAddress(selection, field, address) {
  return {
    ...selection,
    [field]: {
      ...selection[field],
      address,
      candidates: [],
      minimumDistanceMeters: null,
      stationId: null,
    },
  };
}

export function setSnapCandidates(selection, field, result) {
  const stationId = field === "origin"
    ? result.candidates[0]?.station.stationId ?? null
    : null;
  return {
    ...selection,
    [field]: {
      ...selection[field],
      candidates: result.candidates,
      minimumDistanceMeters: result.minimumDistanceMeters,
      stationId,
    },
  };
}

export function setSnapUnavailable(selection, field, minimumDistanceMeters) {
  return {
    ...selection,
    [field]: {
      ...selection[field],
      candidates: [],
      minimumDistanceMeters,
      stationId: null,
    },
  };
}

export function selectOriginStation(selection, stationId) {
  if (!selection.origin.candidates.some(
    candidate => candidate.station.stationId === stationId,
  )) {
    throw new RangeError("Origin station must be within the walking limit");
  }
  return {
    ...selection,
    origin: { ...selection.origin, stationId },
  };
}

export function setWalkLimit(selection, field, maxWalkMeters) {
  if (!Number.isInteger(maxWalkMeters)
      || maxWalkMeters < 100
      || maxWalkMeters > 2_000) {
    throw new RangeError("Walking limit must be between 100 and 2000 metres");
  }
  return {
    ...selection,
    [field]: {
      ...selection[field],
      maxWalkMeters,
      candidates: [],
      minimumDistanceMeters: null,
      stationId: null,
    },
  };
}

export function validateAddressSelection(selection) {
  const errors = {};
  if (!selection.origin.address || !selection.origin.stationId) {
    errors.origin = "Defina o endereço e a parada de origem.";
  }
  if (!selection.destination.address) {
    errors.destination = "Escolha um endereço de destino da lista.";
  } else if (selection.destination.candidates.length === 0) {
    errors.destination = "Nenhuma parada disponível dentro do limite de destino.";
  }
  const departureTime = normalizeDepartureTime(selection.departureTime);
  if (departureTime === null) {
    errors.departureTime = "Use HH:MM, sem segundos, com minutos entre 00 e 59.";
  }
  if (Object.keys(errors).length > 0) return { errors, query: null };
  return {
    errors,
    query: {
      mode: "address",
      origin: {
        ...selection.origin.address,
        maxWalkMeters: selection.origin.maxWalkMeters,
        stationId: selection.origin.stationId,
      },
      destination: {
        ...selection.destination.address,
        maxWalkMeters: selection.destination.maxWalkMeters,
      },
      departureTime,
    },
  };
}
