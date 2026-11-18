import assert from "node:assert/strict";
import test from "node:test";
import { getFlipTransform } from "../js/map-expansion.js";

test("maps the expanded panel back to the compact map rectangle", () => {
  const compact = { left: 456, top: 96, width: 800, height: 600 };
  const expanded = { left: 16, top: 16, width: 1248, height: 688 };

  assert.equal(
    getFlipTransform(compact, expanded),
    "translate(440px, 80px) scale(0.641026, 0.872093)",
  );
});
