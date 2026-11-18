import assert from "node:assert/strict";
import test from "node:test";
import { createFieldActivity } from "../js/field-activity.js";

test("clearing a station leaves map selection inactive until a field is focused", () => {
  const activity = createFieldActivity("origin");

  activity.activate("destination");
  activity.deactivate();
  assert.equal(activity.activeField, null);

  activity.activate("origin");
  assert.equal(activity.activeField, "origin");
});
