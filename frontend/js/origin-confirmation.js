export function createOriginConfirmation(onConfirm) {
  let confirmedId = null;
  return {
    leave(station) {
      if (!station || station.stationId === confirmedId) return false;
      confirmedId = station.stationId;
      onConfirm(station);
      return true;
    },
    reset() {
      confirmedId = null;
    },
  };
}
