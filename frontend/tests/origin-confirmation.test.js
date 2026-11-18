import assert from "node:assert/strict";
import test from "node:test";
import { createOriginConfirmation } from "../js/origin-confirmation.js";

const first = { stationId: "001", label: "Central" };
const second = { stationId: "002", label: "Terminal" };

test("confirms each selected origin only once", () => {
  const confirmed = [];
  const controller = createOriginConfirmation(station => confirmed.push(station.stationId));

  assert.equal(controller.leave(null), false);
  assert.equal(controller.leave(first), true);
  assert.equal(controller.leave(first), false);
  assert.deepEqual(confirmed, ["001"]);
});

test("allows confirmation again after an edit or clear", () => {
  const confirmed = [];
  const controller = createOriginConfirmation(station => confirmed.push(station.stationId));

  controller.leave(first);
  controller.reset();
  assert.equal(controller.leave(first), true);
  assert.equal(controller.leave(second), true);
  assert.deepEqual(confirmed, ["001", "001", "002"]);
});
