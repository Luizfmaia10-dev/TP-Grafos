import assert from "node:assert/strict";
import test from "node:test";
import { buildRouteSegments, createStationMap, projectStation } from "../js/map.js";

const stations = [
  { stationId: "001", longitude: -43.96700111, latitude: -19.84347457 },
  { stationId: "002", longitude: -43.93817059, latitude: -19.9157808 },
  { stationId: "003", longitude: -43.94189701, latitude: -19.9176435 },
];

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
      getBoundingClientRect() { return { left: 0, right: 960, top: 0, bottom: 780 }; },
      querySelector(selector) { return nodes.get(selector); },
    };
  }
  const nodes = new Map([
    "#map-route", "#map-key-station", "#map-key-route", "#map-key-label", "#map-key-short",
    ".network-image--desktop", ".network-image--mobile",
  ].map(selector => [selector, node()]));
  const container = node();
  const layer = node();
  layer.clientWidth = 960;
  layer.parentElement = node();
  container.parentElement = layer;
  let mobile = false;
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
    resizeToMobile() { mobile = true; layer.clientWidth = 358; resize(); },
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

test("map creates safe SVG lines per modal and resets route and legend", t => {
  const { container, find } = createMapFixture(t);
  const map = createStationMap(container, () => {});
  map.setStations(routeStations);
  map.update(selection, null, result);
  const route = find("#map-route");
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
  assert.equal(container.children[1].disabled, true);
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
