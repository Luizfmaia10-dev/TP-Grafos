import assert from "node:assert/strict";
import test from "node:test";
import { describeWalkLimit, walkLimitProgress } from "../js/snap-controls.js";

test("walking visual progress follows every metre across the supported interval", () => {
  assert.equal(walkLimitProgress(100), 0);
  assert.equal(walkLimitProgress(1_050), 0.5);
  assert.equal(walkLimitProgress(2_000), 1);
  assert.equal(walkLimitProgress(847), 747 / 1_900);
});

test("limit modal allows saving a limit before its address exists", () => {
  assert.deepEqual(describeWalkLimit({
    address: null,
    maxWalkMeters: 800,
    minimumDistanceMeters: null,
    candidates: [],
  }, "destination"), {
    state: "missing-address",
    canConfirm: true,
    message: "Endereço de destino ainda não informado. Você pode salvar este limite agora.",
  });
});

test("limit modal shows the minimum distance and blocks an insufficient limit", () => {
  assert.deepEqual(describeWalkLimit({
    address: { label: "Rua A" },
    maxWalkMeters: 300,
    minimumDistanceMeters: 340,
    candidates: [],
  }, "origin"), {
    state: "insufficient",
    canConfirm: false,
    message: "Nenhuma parada dentro de 300 m. Distância mínima necessária: 340 m.",
  });
});

test("limit modal reports candidates without allowing station selection", () => {
  assert.deepEqual(describeWalkLimit({
    address: { label: "Rua A" },
    maxWalkMeters: 800,
    minimumDistanceMeters: 340,
    candidates: [{}, {}, {}],
  }, "origin"), {
    state: "ready",
    canConfirm: true,
    message: "3 paradas dentro do limite. Distância mínima necessária: 340 m.",
  });
});

test("limit modal blocks confirmation when no station exists within two kilometres", () => {
  assert.deepEqual(describeWalkLimit({
    address: { label: "Rua A" },
    maxWalkMeters: 2_000,
    minimumDistanceMeters: null,
    candidates: [],
  }, "destination"), {
    state: "unavailable",
    canConfirm: false,
    message: "Nenhuma parada foi encontrada em até 2 km desse endereço.",
  });
});
