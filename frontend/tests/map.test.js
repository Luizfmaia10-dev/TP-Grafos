import assert from "node:assert/strict";
import test from "node:test";
import { DEMO_STATIONS } from "../js/demo-data.js";
import { projectStation } from "../js/map.js";

// Reference positions from the two Figma coordinate planes, in native SVG pixels.
for (const [layout, positions] of Object.entries({
  desktop: [[406.95, 191.33], [557.37, 533.15], [537.93, 541.95]],
  mobile: [[148.44, 53.51], [232.35, 184.79], [221.50, 188.18]],
})) {
  DEMO_STATIONS.forEach((station, index) => {
    test(`${station.stationId} aligns with the ${layout} Figma map`, () => {
      const point = projectStation(station, layout);
      assert.ok(Math.abs(point.x - positions[index][0]) < 0.01);
      assert.ok(Math.abs(point.y - positions[index][1]) < 0.01);
    });
  });
}
