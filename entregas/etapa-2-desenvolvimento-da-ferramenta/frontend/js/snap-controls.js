const MIN_WALK_METERS = 100;
const MAX_WALK_METERS = 2_000;

export function walkLimitProgress(value) {
  const progress = (value - MIN_WALK_METERS)
    / (MAX_WALK_METERS - MIN_WALK_METERS);
  return Math.min(1, Math.max(0, progress));
}

export function describeWalkLimit(point, field) {
  const fieldName = field === "origin" ? "origem" : "destino";
  if (!point.address) {
    return {
      state: "missing-address",
      canConfirm: true,
      message: `Endereço de ${fieldName} ainda não informado. Você pode salvar este limite agora.`,
    };
  }
  if (point.minimumDistanceMeters != null
      && point.minimumDistanceMeters > point.maxWalkMeters) {
    return {
      state: "insufficient",
      canConfirm: false,
      message: `Nenhuma parada dentro de ${point.maxWalkMeters} m. Distância mínima necessária: ${point.minimumDistanceMeters} m.`,
    };
  }
  if (point.candidates.length === 0 && point.minimumDistanceMeters == null) {
    return {
      state: "unavailable",
      canConfirm: false,
      message: "Nenhuma parada foi encontrada em até 2 km desse endereço.",
    };
  }
  const count = point.candidates.length;
  return {
    state: "ready",
    canConfirm: true,
    message: `${count} ${count === 1 ? "parada" : "paradas"} dentro do limite. Distância mínima necessária: ${point.minimumDistanceMeters} m.`,
  };
}
