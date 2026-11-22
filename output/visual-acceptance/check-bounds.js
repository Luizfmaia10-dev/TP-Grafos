async page => {
  return page.evaluate(() => {
    const map = document.querySelector('.map-panel');
    const selected = [...document.querySelectorAll('button[aria-pressed="true"]')];
    const rect = (element) => {
      const bounds = element.getBoundingClientRect();
      return {
        x: bounds.x,
        y: bounds.y,
        width: bounds.width,
        height: bounds.height,
        right: bounds.right,
        bottom: bounds.bottom,
      };
    };

    const mapRect = map ? rect(map) : null;
    const selectedRects = selected.map((element) => ({
        label: element.getAttribute('aria-label'),
        rect: rect(element),
      }));
    return {
      map: mapRect,
      selected: selectedRects,
      allSelectedInsideMap: Boolean(mapRect) && selectedRects.every(({ rect: selectedRect }) => (
        selectedRect.x >= mapRect.x
        && selectedRect.y >= mapRect.y
        && selectedRect.right <= mapRect.right
        && selectedRect.bottom <= mapRect.bottom
      )),
      reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
    };
  });
}
