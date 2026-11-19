/** Own the autocomplete request lifetime independently from the selected station. */
export function createStationRequest(search, onChange) {
  let state = { status: "idle" };
  let controller = null;
  let version = 0;

  function publish(next) {
    state = next;
    onChange(state);
  }

  return {
    get state() { return state; },
    cancel() {
      version++;
      controller?.abort();
      controller = null;
      publish({ status: "idle" });
    },
    async submit(query) {
      const currentVersion = ++version;
      controller?.abort();
      const currentController = new AbortController();
      controller = currentController;
      publish({ status: "loading", query });
      try {
        const stations = await search(query, { signal: currentController.signal });
        if (currentVersion === version) {
          publish({ status: stations.length ? "ready" : "empty", query, stations });
        }
      } catch (error) {
        if (currentVersion === version && !currentController.signal.aborted) {
          publish({ status: "error", query, error });
        }
      } finally {
        if (currentVersion === version) controller = null;
      }
    },
  };
}
