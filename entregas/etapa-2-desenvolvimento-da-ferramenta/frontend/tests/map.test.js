import assert from "node:assert/strict";
import test from "node:test";
import { buildRouteSegments, createStationMap, projectStation } from "../js/map.js";
import * as mapState from "../js/map.js";

const stations = [
  { stationId: "001", longitude: -43.96700111, latitude: -19.84347457 },
  { stationId: "002", longitude: -43.93817059, latitude: -19.9157808 },
  { stationId: "003", longitude: -43.94189701, latitude: -19.9176435 },
];

const labelPanel = { left: 100, right: 458, top: 50, bottom: 306 };

function translatedRect(rect, translation) {
  return {
    left: rect.left + translation.x, right: rect.right + translation.x,
    top: rect.top + translation.y, bottom: rect.bottom + translation.y,
  };
}

function assertContained(rect, panel = labelPanel) {
  assert.ok(rect.left >= panel.left + 12 && rect.right <= panel.right - 12);
  assert.ok(rect.top >= panel.top + 12 && rect.bottom <= panel.bottom - 12);
}

for (const [edge, rect, expected] of [
  ["top", { left: 150, right: 250, top: 20, bottom: 64 }, { x: 0, y: 42 }],
  ["bottom", { left: 150, right: 250, top: 280, bottom: 324 }, { x: 0, y: -30 }],
  ["left", { left: 80, right: 180, top: 100, bottom: 144 }, { x: 32, y: 0 }],
  ["right", { left: 400, right: 500, top: 100, bottom: 144 }, { x: -54, y: 0 }],
]) {
  test(`label translation contains the ${edge} edge with 12px padding`, () => {
    assert.equal(typeof mapState.calculateLabelTranslations, "function");
    const translations = mapState.calculateLabelTranslations(labelPanel, [Object.freeze(rect)]);
    assert.deepEqual(translations, [expected]);
    assertContained(translatedRect(rect, translations[0]));
  });
}

test("nearby A/B labels prefer above/below their markers regardless of input order", () => {
  assert.equal(typeof mapState.calculateLabelTranslations, "function");
  const markerRect = Object.freeze({ left: 220, right: 264, top: 150, bottom: 194 });
  const labels = ["destination", "origin"].map(role => Object.freeze({
    left: 250, right: 350, top: 160, bottom: 204, role, markerRect,
  }));
  const translations = mapState.calculateLabelTranslations(labelPanel, Object.freeze(labels));
  const [destination, origin] = labels.map((rect, index) => translatedRect(rect, translations[index]));
  assert.equal(origin.bottom, 136);
  assert.equal(destination.top, 208);
  assertContained(origin);
  assertContained(destination);
});

test("colliding A/B labels at the lower edge stay separated inside the panel", () => {
  assert.equal(typeof mapState.calculateLabelTranslations, "function");
  const labels = ["origin", "destination"].map(role => ({
    left: 300, right: 420, top: 280, bottom: 324, role,
    markerRect: { left: 280, right: 324, top: 260, bottom: 304 },
  }));
  const translations = mapState.calculateLabelTranslations(labelPanel, labels);
  const [origin, destination] = labels.map((rect, index) => translatedRect(rect, translations[index]));
  assertContained(origin);
  assertContained(destination);
  assert.ok(origin.bottom + 14 <= destination.top || destination.bottom + 14 <= origin.top
    || origin.right + 14 <= destination.left || destination.right + 14 <= origin.left);
});

test("dense label sets use free space without pushing labels outside the panel", () => {
  assert.equal(typeof mapState.calculateLabelTranslations, "function");
  const panel = { left: 0, right: 960, top: 0, bottom: 660 };
  const labels = Array.from({ length: 20 }, () => ({ left: 400, right: 500, top: 300, bottom: 344 }));
  const translations = mapState.calculateLabelTranslations(panel, labels);
  assert.equal(translations.length, 20);
  const placed = labels.map((rect, index) => translatedRect(rect, translations[index]));
  placed.forEach((rect, index) => {
    assertContained(rect, panel);
    for (const previous of placed.slice(0, index)) {
      assert.ok(rect.right + 14 <= previous.left || previous.right + 14 <= rect.left
        || rect.bottom + 14 <= previous.top || previous.bottom + 14 <= rect.top);
    }
  });
  assert.deepEqual(mapState.calculateLabelTranslations(panel, []), []);
});

test("suggestion labels appear only on hover or focus while A/B remain visible", t => {
  const { container } = createMapFixture(t);
  const map = createStationMap(container, () => {});
  const suggestions = Array.from({ length: 20 }, (_, index) => ({
    ...routeStations[index % 4], stationId: String(index),
  }));
  map.setStations(suggestions);
  map.update({ originId: "0", destinationId: "1" }, "origin");
  const labels = container.children.map(button => button.children[1]);
  assert.deepEqual(labels.map(label => label.hidden), [false, false, ...Array(18).fill(true)]);
  const button = container.children[2];
  const position = { ...button.style };
  const accessibleName = button.attributes["aria-label"];
  button.events.mouseenter();
  assert.equal(labels[2].hidden, false);
  button.events.focus();
  button.events.mouseleave();
  assert.equal(labels[2].hidden, false);
  button.events.blur();
  assert.equal(labels[2].hidden, true);
  assert.equal(button.children[0].children[0].hidden, false);
  assert.equal(button.attributes["aria-label"], accessibleName);
  assert.ok(accessibleName.includes(suggestions[2].label));
  assert.deepEqual(button.style, position);
});

test("unselected suggestions retain their markers alongside a route result", t => {
  const { container } = createMapFixture(t);
  const map = createStationMap(container, () => {});
  const suggestion = { ...routeStations[1], stationId: "suggestion" };
  map.setStations([...routeStations, suggestion]);
  map.update(selection, null, result);
  const button = container.children.at(-1);
  assert.equal(button.children[0].children[0].hidden, false);
  assert.equal(button.children[1].hidden, true);
  assert.equal(button.attributes["aria-label"], suggestion.label);
  assert.equal(container.children[0].children[1].hidden, false);
  assert.equal(container.children[3].children[1].hidden, false);
});

test("route stations allow inspection by focus while blocking selection until editing", t => {
  const { container } = createMapFixture(t);
  const selected = [];
  const map = createStationMap(container, station => selected.push(station.stationId));
  map.setStations(routeStations);
  map.update(selection, null, result);
  const button = container.children[1];
  assert.equal(button.disabled, false);
  assert.equal(button.attributes["aria-disabled"], "true");
  button.events.focus();
  assert.equal(button.children[1].hidden, false);
  assert.equal(button.attributes["aria-label"], routeStations[1].label);
  button.events.click();
  assert.deepEqual(selected, []);
  map.update(selection, "destination");
  assert.equal(button.attributes["aria-disabled"], "false");
  button.events.click();
  assert.deepEqual(selected, [routeStations[1].stationId]);
  map.update(selection, null);
  button.events.click();
  assert.deepEqual(selected, [routeStations[1].stationId]);
});

// Reference positions from the two Figma coordinate planes, in native SVG pixels.
for (const [layout, positions] of Object.entries({
  desktop: [[406.95, 191.33], [557.37, 533.15], [537.93, 541.95]],
  mobile: [[148.44, 53.51], [232.35, 184.79], [221.50, 188.18]],
})) {
  stations.forEach((station, index) => {
    test(`${station.stationId} aligns with the ${layout} Figma map`, () => {
      const point = projectStation(station, layout);
      assert.ok(Math.abs(point.x - positions[index][0]) < 0.01);
      assert.ok(Math.abs(point.y - positions[index][1]) < 0.01);
    });
  });
}

for (const [layout, bounds, expected] of [
  ["desktop", [-44.045, -43.861, -19.803, -19.968], ["0,0 960,0", "960,0 960,780", "960,780 0,780"]],
  ["mobile", [-44.018, -43.895, -19.814, -19.955], ["0,0 358,0", "358,0 358,256", "358,256 0,256"]],
]) {
  test(`route segments keep each modal and its exact ${layout} endpoints`, () => {
    const [west, east, north, south] = bounds;
    const points = [
      { longitude: west, latitude: north }, { longitude: east, latitude: north },
      { longitude: east, latitude: south }, { longitude: west, latitude: south },
    ];
    const steps = ["BUS", "SUBWAY", "WALK"].map((vehicleType, index) => ({
      vehicleType, origin: points[index], destination: points[index + 1],
    }));
    assert.deepEqual(buildRouteSegments(steps, layout), [
      { mode: "bus", points: expected[0] },
      { mode: "subway", points: expected[1] },
      { mode: "walk", points: expected[2] },
    ]);
  });
}

test("route segments stay empty without steps", () => {
  assert.deepEqual(buildRouteSegments([], "desktop"), []);
});

const outOfBoundsSteps = [{
  vehicleType: "BUS",
  origin: { longitude: -44.02171289, latitude: -19.97429891 },
  destination: { longitude: -44.02377811, latitude: -19.97580814 },
}];

for (const [layout, width, height, west, east, north, south] of [
  ["desktop", 960, 780, -44.045, -43.861, -19.803, -19.968],
  ["mobile", 358, 256, -44.018, -43.895, -19.814, -19.955],
]) {
  test(`empty and in-bounds routes preserve the exact ${layout} viewport`, () => {
    assert.equal(typeof mapState.fitRouteViewport, "function");
    const base = { x: 0, y: 0, width, height };
    assert.deepEqual(mapState.fitRouteViewport([], layout), base);
    assert.deepEqual(mapState.fitRouteViewport([{
      vehicleType: "BUS",
      origin: { longitude: west, latitude: north },
      destination: { longitude: east, latitude: south },
    }], layout), base);
  });

  test(`real out-of-bounds route fits with padding and the ${layout} aspect ratio`, () => {
    assert.equal(typeof mapState.fitRouteViewport, "function");
    const viewport = mapState.fitRouteViewport(outOfBoundsSteps, layout);
    assert.ok(Math.abs(viewport.width / viewport.height - width / height) < 1e-9);
    assert.ok(viewport.x <= 0 && viewport.y <= 0);
    assert.ok(viewport.x + viewport.width >= width);
    assert.ok(viewport.y + viewport.height >= height);
    for (const station of [outOfBoundsSteps[0].origin, outOfBoundsSteps[0].destination]) {
      const point = projectStation(station, layout);
      assert.ok(point.x - viewport.x >= 24);
      assert.ok(point.y - viewport.y >= 24);
      assert.ok(viewport.x + viewport.width - point.x >= 24);
      assert.ok(viewport.y + viewport.height - point.y >= 24);
    }
    if (layout === "desktop") assert.ok(viewport.y + viewport.height > 816.91 + 23);
  });
}

function createMapFixture(t) {
  const previous = { document: globalThis.document, window: globalThis.window, ResizeObserver: globalThis.ResizeObserver };
  const document = {
    createElement: tagName => node(tagName),
    createElementNS: (namespaceURI, tagName) => node(tagName, namespaceURI),
    querySelector: selector => nodes.get(selector),
  };
  function node(tagName = "div", namespaceURI = null) {
    return {
      tagName, namespaceURI, ownerDocument: document, children: [], attributes: {},
      style: {}, dataset: {}, events: {}, textContent: "", hidden: false,
      append(...children) { this.children.push(...children); },
      replaceChildren(...children) { this.children = children; },
      setAttribute(name, value) { this.attributes[name] = value; },
      toggleAttribute(name, force) { if (force) this.attributes[name] = ""; else delete this.attributes[name]; },
      addEventListener(type, callback) { this.events[type] = callback; },
      getClientRects() { return []; },
      getBoundingClientRect() {
        if (tagName === "button") {
          const layer = container.parentElement.getBoundingClientRect();
          const x = layer.left + Number.parseFloat(this.style.left || "0") / 100 * layer.width;
          const y = layer.top + Number.parseFloat(this.style.top || "0") / 100 * layer.height;
          return { left: x - 22, right: x + 22, top: y - 22, bottom: y + 22, width: 44, height: 44 };
        }
        return { left: 0, right: 960, top: 0, bottom: 780, width: 960, height: 780 };
      },
      querySelector(selector) { return nodes.get(selector); },
    };
  }
  const nodes = new Map([
    "#map-route", "#map-key-station", "#map-key-route", "#map-key-label", "#map-key-short",
    ".network-background", ".network-image--desktop", ".network-image--mobile",
  ].map(selector => [selector, node()]));
  const container = node();
  const layer = node();
  let panelWidth = 960;
  let panelHeight = 780;
  let mobile = false;
  layer.parentElement = node();
  layer.parentElement.getBoundingClientRect = () => ({
    left: 0, top: 0, right: panelWidth, bottom: panelHeight, width: panelWidth, height: panelHeight,
  });
  // Mirror the existing centered cover layer unless render sets explicit dimensions.
  Object.defineProperties(layer, {
    clientWidth: { get: () => Number.parseFloat(layer.style.width)
      || Math.max(panelWidth, panelHeight * (mobile ? 358 / 256 : 960 / 780)) },
    clientHeight: { get: () => Number.parseFloat(layer.style.height)
      || Math.max(panelHeight, panelWidth * (mobile ? 256 / 358 : 780 / 960)) },
  });
  layer.getBoundingClientRect = () => ({
    left: (panelWidth - layer.clientWidth) / 2, top: (panelHeight - layer.clientHeight) / 2,
    right: (panelWidth + layer.clientWidth) / 2, bottom: (panelHeight + layer.clientHeight) / 2,
    width: layer.clientWidth, height: layer.clientHeight,
  });
  container.parentElement = layer;
  let resize;
  globalThis.document = document;
  globalThis.window = { matchMedia: () => ({ matches: mobile }) };
  globalThis.ResizeObserver = class {
    constructor(callback) { resize = callback; }
    observe() {}
  };
  t.after(() => Object.assign(globalThis, previous));
  return {
    container, find: selector => nodes.get(selector),
    resizeToMobile() { mobile = true; panelWidth = 358; panelHeight = 256; resize(); },
    resizePanel(width, height) { panelWidth = width; panelHeight = height; resize(); },
  };
}

const routeStations = [
  { stationId: "001", name: "Northwest", label: "Northwest", mapName: "Northwest", shortName: "NW", longitude: -44.045, latitude: -19.803 },
  { stationId: "002", name: "Northeast", label: "Northeast", mapName: "Northeast", shortName: "NE", longitude: -43.861, latitude: -19.803 },
  { stationId: "003", name: "Southeast", label: "Southeast", mapName: "Southeast", shortName: "SE", longitude: -43.861, latitude: -19.968 },
  { stationId: "004", name: "Southwest", label: "Southwest", mapName: "Southwest", shortName: "SW", longitude: -44.045, latitude: -19.968 },
];
const result = {
  origin: routeStations[0], destination: routeStations[3],
  steps: ["BUS", "SUBWAY", "WALK"].map((vehicleType, index) => ({
    vehicleType, origin: routeStations[index], destination: routeStations[index + 1],
  })),
};
const selection = { originId: "001", destinationId: "004" };

test("successive searches replace old suggestions while keeping selections and current route", () => {
  assert.equal(typeof mapState.currentMapStations, "function");
  const current = mapState.currentMapStations;
  let registry = current([], [routeStations[0], routeStations[1]], {}, null);
  registry = current(registry, [routeStations[2]], { originId: "001" }, null);
  assert.deepEqual(registry.map(station => station.stationId), ["001", "003"]);
  registry = current(registry, [routeStations[3]], { originId: "001", destinationId: "003" }, result);
  assert.deepEqual(new Set(registry.map(station => station.stationId)), new Set(["001", "002", "003", "004"]));
  registry = current(registry, [], { originId: "001", destinationId: "003" }, null);
  assert.deepEqual(registry.map(station => station.stationId), ["001", "003"]);
});

test("station registry replaces controls, deduplicates IDs and keeps station selection", t => {
  const { container, resizeToMobile } = createMapFixture(t);
  const selected = [];
  const map = createStationMap(container, station => selected.push(station));
  map.setStations([routeStations[0], routeStations[0], routeStations[1]]);
  assert.deepEqual(container.children.map(button => button.dataset.stationId), ["001", "002"]);
  container.children[0].events.click();
  assert.deepEqual(selected, [routeStations[0]]);
  map.update(selection, "origin");
  assert.equal(container.children[0].dataset.selection, "origin");
  assert.equal(container.children[0].attributes["aria-pressed"], "true");
  assert.equal(container.children[1].disabled, false);
  const oldControl = container.children[0];
  map.setStations([routeStations[3]]);
  assert.equal(container.children.length, 1);
  assert.notEqual(container.children[0], oldControl);
  assert.equal(container.children[0].dataset.selection, "destination");
  assert.equal(container.children[0].style.left, "0%");
  assert.equal(container.children[0].style.top, "100%");
  resizeToMobile();
  assert.notEqual(container.children[0].style.left, "0%");
});

test("unchanged station registry keeps the active map control", t => {
  const { container } = createMapFixture(t);
  const map = createStationMap(container, () => {});
  map.setStations([{ ...routeStations[0] }]);
  const control = container.children[0];

  map.setStations([routeStations[0]]);

  assert.equal(container.children[0], control);
});

test("map creates safe SVG lines per modal and resets route and legend", t => {
  const { container, find } = createMapFixture(t);
  const map = createStationMap(container, () => {});
  map.setStations(routeStations);
  map.update(selection, null, result);
  const route = find("#map-route");
  assert.equal(route.attributes.viewBox, "0 0 960 780");
  assert.equal(route.children.length, 6);
  assert.deepEqual(route.children.map(line => line.attributes.class), [
    "route-glow route-segment--bus", "route-line route-segment--bus",
    "route-glow route-segment--subway", "route-line route-segment--subway",
    "route-glow route-segment--walk", "route-line route-segment--walk",
  ]);
  assert.deepEqual(route.children.map(line => line.attributes.points), [
    "0,0 960,0", "0,0 960,0", "960,0 960,780", "960,0 960,780", "960,780 0,780", "960,780 0,780",
  ]);
  assert.deepEqual(route.children.map(line => line.attributes["stroke-linecap"]), [
    "round", "round", "round", "round", "butt", "butt",
  ]);
  assert.ok(route.children.every(line => line.tagName === "polyline"
    && line.namespaceURI === "http://www.w3.org/2000/svg" && line.attributes.fill === "none"));
  assert.deepEqual(find("#map-key-route").children.map(item => item.dataset.mode), ["bus", "subway", "walk"]);
  assert.equal(container.children[1].dataset.onRoute, "true");
  assert.equal(container.children[1].disabled, false);
  assert.equal(container.children[1].attributes["aria-disabled"], "true");
  map.update(selection, null, { ...result, steps: [result.steps[2], result.steps[2]] });
  assert.equal(route.children.length, 4);
  assert.deepEqual(find("#map-key-route").children.map(item => item.dataset.mode), ["walk"]);
  map.update(selection, "destination");
  assert.equal(route.children.length, 0);
  assert.equal(route.attributes.hidden, "");
  assert.equal(find("#map-key-route").children.length, 0);
  assert.equal(find("#map-key-route").hidden, true);
  assert.equal(find("#map-key-station").hidden, false);
});

test("map backdrop is active only while a route result is visible", t => {
  const { container } = createMapFixture(t);
  const map = createStationMap(container, () => {});
  const panel = container.parentElement.parentElement;
  const selection = { originId: "001", destinationId: "002" };
  const result = {
    origin: routeStations[0],
    destination: routeStations[1],
    steps: [{ vehicleType: "BUS", origin: routeStations[0], destination: routeStations[1] }],
  };
  map.setStations(routeStations.slice(0, 2));

  map.update(selection, "origin");
  assert.equal(panel.dataset.routeResult, "false");
  map.update(selection, null, result);
  assert.equal(panel.dataset.routeResult, "true");
  map.update(selection, "destination");
  assert.equal(panel.dataset.routeResult, "false");
  map.update({}, null);
  assert.equal(panel.dataset.routeResult, "false");
});

for (const [layout, width, height] of [["desktop", 960, 780], ["mobile", 358, 256]]) {
  test(`expanded ${layout} viewport aligns route, background and markers and resets on editing`, t => {
    const { container, find, resizeToMobile } = createMapFixture(t);
    const map = createStationMap(container, () => {});
    const points = [outOfBoundsSteps[0].origin, outOfBoundsSteps[0].destination]
      .map((point, index) => ({ ...routeStations[index], ...point }));
    const routeResult = {
      origin: points[0], destination: points[1],
      steps: [{ vehicleType: "BUS", origin: points[0], destination: points[1] }],
    };
    const routeSelection = { originId: "001", destinationId: "002" };
    map.setStations(points);
    map.update(routeSelection, null, routeResult);
    if (layout === "mobile") resizeToMobile();

    const viewport = mapState.fitRouteViewport(routeResult.steps, layout);
    const route = find("#map-route");
    assert.equal(route.attributes.viewBox, `${viewport.x} ${viewport.y} ${viewport.width} ${viewport.height}`);
    const background = find(".network-background");
    assert.match(background.style.transform, /^matrix\(/u);
    assert.equal(background.style.transformOrigin, "top left");
    const matrix = background.style.transform.slice(7, -1).split(",").map(Number);
    const scale = width / viewport.width;
    const layerRect = container.parentElement.getBoundingClientRect();
    const screenScale = layerRect.width / viewport.width;
    assert.deepEqual(matrix.slice(0, 4), [scale, 0, 0, scale]);
    assert.ok(Math.abs(matrix[4] + viewport.x * screenScale) < 1e-9);
    assert.ok(Math.abs(matrix[5] + viewport.y * screenScale) < 1e-9);
    for (const [index, button] of container.children.entries()) {
      const left = Number.parseFloat(button.style.left);
      const top = Number.parseFloat(button.style.top);
      assert.ok(left >= 0 && left <= 100);
      assert.ok(top >= 0 && top <= 100);
      const point = projectStation(points[index], layout);
      assert.ok(Math.abs(left / 100 * layerRect.width - (point.x * screenScale + matrix[4])) < 1e-9);
      assert.ok(Math.abs(top / 100 * layerRect.height - (point.y * screenScale + matrix[5])) < 1e-9);
    }

    map.update(routeSelection, "origin");
    assert.equal(route.attributes.viewBox, `0 0 ${width} ${height}`);
    assert.equal(background.style.transform, "matrix(1, 0, 0, 1, 0, 0)");
    assert.equal(route.children.length, 0);
    assert.equal(route.attributes.hidden, "");
    const position = projectStation(points[0], layout);
    assert.equal(container.children[0].style.left, `${position.x * 100 / width}%`);
    assert.equal(container.children[0].style.top, `${position.y * 100 / height}%`);
  });
}

test("route label density uses the expanded viewport scale", t => {
  const { container } = createMapFixture(t);
  const map = createStationMap(container, () => {});
  const points = [
    { ...routeStations[0], longitude: -44.045, latitude: -19.803 },
    { ...routeStations[1], longitude: -44.0266, latitude: -19.803 },
    { ...routeStations[2], longitude: -42.205, latitude: -19.803 },
  ];
  map.setStations(points);
  map.update({ originId: "001", destinationId: "002" }, null, {
    origin: points[0], destination: points[1],
    steps: [
      { vehicleType: "BUS", origin: points[0], destination: points[2] },
      { vehicleType: "BUS", origin: points[2], destination: points[1] },
    ],
  });
  assert.equal(container.dataset.dense, "true");
  assert.equal(container.children[0].children[1].children[0].children[0].textContent, "A · Northwest");
});

for (const [layout, width, height, ratio] of [
  ["desktop", 960, 660, 960 / 780], ["desktop", 660, 960, 960 / 780],
  ["mobile", 358, 200, 358 / 256], ["mobile", 200, 358, 358 / 256],
]) {
  test(`complete 44x44 markers remain inside the visible ${width}x${height} ${layout} panel`, t => {
    const { container, resizePanel, resizeToMobile } = createMapFixture(t);
    const map = createStationMap(container, () => {});
    const points = [outOfBoundsSteps[0].origin, outOfBoundsSteps[0].destination]
      .map((point, index) => ({ ...routeStations[index], ...point }));
    const routeSelection = { originId: "001", destinationId: "002" };
    map.setStations(points);
    map.update(routeSelection, "origin");
    if (layout === "mobile") resizeToMobile();
    resizePanel(width, height);
    const layer = container.parentElement;
    const cover = layer.getBoundingClientRect();
    if (width === 960 && height === 660) {
      assert.equal(cover.width, 960);
      assert.equal(cover.height, 780);
      assert.equal(cover.top, -60);
    }

    map.update(routeSelection, null, {
      origin: points[0], destination: points[1],
      steps: [{ vehicleType: "BUS", origin: points[0], destination: points[1] }],
    });
    const rect = layer.getBoundingClientRect();
    for (const button of container.children) {
      const marker = button.getBoundingClientRect();
      assert.equal(marker.width, 44);
      assert.equal(marker.height, 44);
      assert.ok(marker.left >= 0 && marker.right <= width,
        `marker box [${marker.left}, ${marker.right}] is outside the panel width ${width}`);
      assert.ok(marker.top >= 0 && marker.bottom <= height,
        `marker box [${marker.top}, ${marker.bottom}] is outside the panel height ${height}`);
    }
    assert.ok(rect.left >= -1e-9 && rect.top >= -1e-9);
    assert.ok(rect.right <= width + 1e-9 && rect.bottom <= height + 1e-9);
    assert.ok(Math.abs(rect.width / rect.height - ratio) < 1e-9);

    map.update(routeSelection, "origin");
    assert.equal(layer.style.width, "");
    assert.equal(layer.style.height, "");
    assert.deepEqual(layer.getBoundingClientRect(), cover);
  });
}

for (const [layout, width, height, nativeWidth, nativeHeight, west, east, north, south] of [
  ["desktop", 960, 660, 960, 780, -44.045, -43.861, -19.803, -19.968],
  ["desktop", 960, 780, 960, 780, -44.045, -43.861, -19.803, -19.968],
  ["mobile", 358, 200, 358, 256, -44.018, -43.895, -19.814, -19.955],
  ["mobile", 358, 256, 358, 256, -44.018, -43.895, -19.814, -19.955],
]) {
  test(`in-bounds edge route keeps complete 44x44 markers inside the ${width}x${height} ${layout} panel`, t => {
    const { container, find, resizePanel, resizeToMobile } = createMapFixture(t);
    const map = createStationMap(container, () => {});
    const points = [
      { ...routeStations[0], longitude: west, latitude: north },
      { ...routeStations[1], longitude: east, latitude: south },
    ];
    const routeSelection = { originId: "001", destinationId: "002" };
    map.setStations(points);
    map.update(routeSelection, "origin");
    if (layout === "mobile") resizeToMobile();
    resizePanel(width, height);
    const layer = container.parentElement;
    const cover = layer.getBoundingClientRect();

    map.update(routeSelection, null, {
      origin: points[0], destination: points[1],
      steps: [{ vehicleType: "BUS", origin: points[0], destination: points[1] }],
    });

    const route = find("#map-route");
    assert.equal(route.attributes.viewBox, `0 0 ${nativeWidth} ${nativeHeight}`);
    assert.equal(route.children[0].attributes.points, `0,0 ${nativeWidth},${nativeHeight}`);
    for (const button of container.children) {
      const marker = button.getBoundingClientRect();
      assert.equal(marker.width, 44);
      assert.equal(marker.height, 44);
      assert.ok(marker.top >= 0 && marker.bottom <= height,
        `marker box [${marker.top}, ${marker.bottom}] is outside the panel height ${height}`);
      assert.ok(marker.left >= 0 && marker.right <= width,
        `marker box [${marker.left}, ${marker.right}] is outside the panel width ${width}`);
    }
    const rect = layer.getBoundingClientRect();
    assert.ok(rect.left >= 0 && rect.top >= 0 && rect.right <= width && rect.bottom <= height);
    assert.ok(Math.abs(rect.width / rect.height - nativeWidth / nativeHeight) < 1e-9);

    for (const [nextSelection, activeField] of [[routeSelection, "origin"], [{}, null]]) {
      map.update(nextSelection, activeField);
      assert.equal(route.attributes.viewBox, `0 0 ${nativeWidth} ${nativeHeight}`);
      assert.equal(route.children.length, 0);
      assert.equal(find(".network-background").style.transform, "matrix(1, 0, 0, 1, 0, 0)");
      assert.equal(layer.style.width, "");
      assert.equal(layer.style.height, "");
      assert.deepEqual(layer.getBoundingClientRect(), cover);
    }
  });
}
