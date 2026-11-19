import assert from "node:assert/strict";
import test from "node:test";
import { buildTimelineEntries, renderRoute } from "../js/route-view.js";

const central = { stationId: "001", name: "Central", mapName: "Central" };
const transfer = { stationId: "002", name: "Integração", mapName: "Integração" };
const terminal = { stationId: "003", name: "Terminal", mapName: "Terminal" };
const destination = { stationId: "004", name: "Destino", mapName: "Destino" };
const result = {
  status: "found", serviceDate: "2026-11-19", origin: central, destination,
  query: { originId: "001", destinationId: "004", departureTime: "25:05" },
  arrivalTime: "25:18:00", totalSeconds: 780, waitingSeconds: 60,
  travelSeconds: 720, distanceKm: 3.2,
  instructions: [
    "Wait at Central until 25:06:00.",
    "Take BUS bus from Central to Integração at 25:06:00; arrive at 25:11:30.",
    "Take SUBWAY metro from Integração to Terminal at 25:11:30; arrive at 25:15:45.",
    "Take WALK walk from Terminal to Destino at 25:15:45; arrive at 25:18:00.",
  ],
  steps: [
    { origin: central, destination: transfer, routeId: "bus", vehicleType: "BUS",
      departureTime: "25:06:00", arrivalTime: "25:11:30", waitingSeconds: 60,
      travelSeconds: 330, distanceKm: 1 },
    { origin: transfer, destination: terminal, routeId: "metro", vehicleType: "SUBWAY",
      departureTime: "25:11:30", arrivalTime: "25:15:45", waitingSeconds: 0,
      travelSeconds: 255, distanceKm: 2 },
    { origin: terminal, destination, routeId: "walk", vehicleType: "WALK",
      departureTime: "25:15:45", arrivalTime: "25:18:00", waitingSeconds: 0,
      travelSeconds: 135, distanceKm: 0.2 },
  ],
};

test("timeline keeps endpoints and consumes a wait instruction before each movement", () => {
  const entries = buildTimelineEntries(result);
  assert.deepEqual(entries.map(entry => entry.kind),
    ["origin", "wait", "bus", "subway", "walk", "destination"]);
  assert.equal(entries[0].time, "25:05");
  assert.equal(entries[0].station, central);
  assert.equal(entries[1].description, result.instructions[0]);
  assert.equal(entries[1].time, "25:06:00");
  assert.equal(entries[1].station, central);
  assert.equal(entries[2].description, result.instructions[1]);
  assert.equal(entries[4].routeId, "walk");
  for (const [index, step] of result.steps.entries()) {
    const entry = entries[index + 2];
    assert.equal(entry.description, result.instructions[index + 1]);
    assert.equal(entry.time, step.departureTime);
    assert.equal(entry.arrivalTime, step.arrivalTime);
    assert.equal(entry.routeId, step.routeId);
    assert.equal(entry.origin, step.origin);
    assert.equal(entry.destination, step.destination);
    assert.equal(entry.station, step.origin);
  }
  assert.deepEqual(entries.slice(2, 5).map(entry => entry.label),
    ["Ônibus", "Metrô", "Caminhada"]);
  assert.equal(entries.at(-1).time, "25:18:00");
  assert.equal(entries.at(-1).station, destination);
});

function createDocument() {
  function node() {
    return {
      textContent: "", className: "", dataset: {}, style: {}, children: [], attributes: {},
      append(...children) { this.children.push(...children); },
      replaceChildren(...children) { this.children = children; },
      setAttribute(name, value) { this.attributes[name] = value; },
    };
  }
  const nodes = new Map([
    "total-minutes", "exact-total", "arrival-time", "exact-arrival", "waiting-duration",
    "vehicle-duration", "waiting-proportion", "route-distance", "itinerary-steps",
  ].map(id => [`#${id}`, node()]));
  return { querySelector: selector => nodes.get(selector), createElement: node };
}

test("renderer fills the multimodal summary and keeps exact service-day times accessible", () => {
  const previousDocument = globalThis.document;
  const document = createDocument();
  globalThis.document = document;
  try {
    renderRoute(result);
    const find = id => document.querySelector(`#${id}`);
    assert.equal(find("total-minutes").textContent, 13);
    assert.equal(find("exact-total").textContent, "Tempo total exato: 13 min.");
    assert.equal(find("arrival-time").textContent, "25:18");
    assert.equal(find("arrival-time").title, "25:18:00");
    assert.equal(find("exact-arrival").textContent, "25:18:00");
    assert.equal(find("waiting-duration").textContent, "1 min de espera");
    assert.equal(find("vehicle-duration").textContent, "12 min em deslocamento");
    assert.equal(find("waiting-proportion").style.width, "7.6923076923076925%");
    assert.equal(find("route-distance").textContent, "≈ 3,2 km");
    const rows = find("itinerary-steps").children;
    assert.deepEqual(rows.map(row => row.className), [
      "itinerary-step itinerary-step--origin", "itinerary-step itinerary-step--wait",
      "itinerary-step itinerary-step--bus", "itinerary-step itinerary-step--subway",
      "itinerary-step itinerary-step--walk", "itinerary-step itinerary-step--destination",
    ]);
    assert.deepEqual(rows.slice(1, 5).map(row => row.children[2].children[1].textContent),
      result.instructions);
    assert.deepEqual(rows.map(row => row.dataset.stationId), ["001", "001", "001", "002", "003", "004"]);
    assert.equal(rows[3].children[0].children[1]?.className, "sr-only");
    assert.deepEqual(rows.map(row => row.children[0].children[0].textContent),
      ["25:05", "25:06", "25:06", "25:11", "25:15", "25:18"]);
    assert.deepEqual(rows.map(row => row.children[0].children[1].textContent),
      ["25:05", "25:06:00", "25:06:00", "25:11:30", "25:15:45", "25:18:00"]);
    for (const row of rows) {
      const clock = row.children[0];
      assert.equal(clock.children[0].attributes["aria-hidden"], "true");
      assert.equal(clock.children[1].className, "sr-only");
      assert.equal(clock.children[1].attributes["aria-hidden"], undefined);
    }
    assert.equal(rows[0].children[0].title, "25:05");
    assert.equal(rows[3].children[0].title, "25:11:30");
    assert.equal(rows[0].children[1].textContent, "A");
    assert.equal(rows.at(-1).children[1].textContent, "B");
    renderRoute(result);
    assert.equal(find("itinerary-steps").children.length, 6);
  } finally {
    globalThis.document = previousDocument;
  }
});
