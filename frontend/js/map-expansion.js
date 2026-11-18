const ratio = (value) => Number(value.toFixed(6));

export function getFlipTransform(from, to) {
  const x = from.left - to.left;
  const y = from.top - to.top;
  const scaleX = ratio(from.width / to.width);
  const scaleY = ratio(from.height / to.height);
  return `translate(${x}px, ${y}px) scale(${scaleX}, ${scaleY})`;
}

export function animateMapLayout(panel, before, duration) {
  const after = panel.getBoundingClientRect();
  if (typeof panel.animate !== "function") return null;
  return panel.animate([
    { transformOrigin: "top left", transform: getFlipTransform(before, after) },
    { transformOrigin: "top left", transform: "none" },
  ], { duration, easing: "cubic-bezier(0.76, 0, 0.24, 1)" });
}
