import assert from "node:assert/strict";
import test from "node:test";
import { maskDepartureTime } from "../js/time-mask.js";

for (const [input, expected] of [
  ["", ""],
  ["0", "0"],
  ["07", "07"],
  ["074", "07:4"],
  ["0745", "07:45"],
  ["2515", "25:15"],
  ["10015", "100:15"],
  ["07:4", "07:4"],
  ["07:45", "07:45"],
  ["07:45:30", "07:45"],
  ["ab07c45", "07:45"],
]) {
  test(`masks ${JSON.stringify(input)} as ${expected}`, () => {
    assert.equal(maskDepartureTime(input), expected);
  });
}
