/** Own the request lifetime so an edited query never receives an older result. */
export function createRouteRequest(search, onChange) {
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
      if (state.status !== "idle") publish({ status: "idle" });
    },
    async submit(query) {
      if (state.status === "loading") return;
      const currentVersion = ++version;
      const currentController = new AbortController();
      controller = currentController;
      publish({ status: "loading" });
      try {
        const result = await search(query, { signal: currentController.signal });
        if (currentVersion === version) publish(result);
      } catch {
        if (currentVersion === version && !currentController.signal.aborted) {
          publish({ status: "error" });
        }
      } finally {
        if (currentVersion === version) controller = null;
      }
    },
  };
}
