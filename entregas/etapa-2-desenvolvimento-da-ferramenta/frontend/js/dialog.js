export function createDialog(element) {
  let trigger = null;
  element.addEventListener("close", () => {
    trigger?.focus();
    trigger = null;
  });
  return {
    get isOpen() { return element.open; },
    open(nextTrigger) {
      trigger = nextTrigger;
      if (!element.open) element.showModal();
    },
    close() {
      if (element.open) element.close();
    },
  };
}
