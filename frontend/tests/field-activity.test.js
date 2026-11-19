import assert from "node:assert/strict";
import test from "node:test";
import { createFieldActivity, shouldCloseStationOptions } from "../js/field-activity.js";

test("clearing a station leaves map selection inactive until a field is focused", () => {
  const activity = createFieldActivity("origin");

  activity.activate("destination");
  activity.deactivate();
  assert.equal(activity.activeField, null);

  activity.activate("origin");
  assert.equal(activity.activeField, "origin");
});

test("pressing a map station keeps options open until the station is selected", () => {
  const fieldWrapper = { contains: () => false };
  const mapStation = { closest: selector => selector === ".map-station" ? {} : null };

  assert.equal(shouldCloseStationOptions(fieldWrapper, mapStation), false);
});

test("pressing outside the field and map closes station options", () => {
  const fieldWrapper = { contains: () => false };
  const outsideTarget = { closest: () => null };

  assert.equal(shouldCloseStationOptions(fieldWrapper, outsideTarget), true);
});
