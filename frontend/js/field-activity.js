export function createFieldActivity(initialField = "origin") {
  let activeField = initialField;
  return {
    get activeField() {
      return activeField;
    },
    activate(field) {
      activeField = field;
    },
    deactivate() {
      activeField = null;
    },
  };
}

export function shouldCloseStationOptions(fieldWrapper, target) {
  return !fieldWrapper.contains(target) && !target.closest?.(".map-station");
}
