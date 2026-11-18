import assert from "node:assert/strict";
import test from "node:test";
import {
  createWheelValues,
  formatPickerTime,
  parsePickerTime,
  stepWheelValue,
} from "../js/time-picker.js";

test("parses only minute-precision service-day times", () => {
  assert.deepEqual(parsePickerTime("07:45"), { hour: 7, minute: 45 });
  assert.deepEqual(parsePickerTime("25:15"), { hour: 25, minute: 15 });
  assert.deepEqual(parsePickerTime("100:05"), { hour: 100, minute: 5 });
  assert.equal(parsePickerTime("07:45:30"), null);
  assert.equal(parsePickerTime("07:60"), null);
});

test("formats a wheel selection without seconds", () => {
  assert.equal(formatPickerTime(7, 5), "07:05");
  assert.equal(formatPickerTime(25, 15), "25:15");
  assert.equal(formatPickerTime(100, 5), "100:05");
});

test("builds padded wheel values and wraps keyboard steps", () => {
  assert.deepEqual(createWheelValues(2), ["00", "01", "02"]);
  assert.equal(stepWheelValue(59, 1, 59), 0);
  assert.equal(stepWheelValue(0, -1, 59), 59);
});
