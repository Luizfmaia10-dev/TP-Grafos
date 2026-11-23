import assert from "node:assert/strict";
import test from "node:test";
import { createDialog } from "../js/dialog.js";

test("dialog opens modally and restores focus to its trigger", () => {
  const events = {};
  const dialogElement = {
    open: false,
    addEventListener(type, callback) { events[type] = callback; },
    showModal() { this.open = true; },
    close() { this.open = false; events.close?.(); },
  };
  let focusCount = 0;
  const trigger = { focus() { focusCount += 1; } };
  const dialog = createDialog(dialogElement);

  dialog.open(trigger);
  assert.equal(dialogElement.open, true);
  dialog.close();

  assert.equal(dialogElement.open, false);
  assert.equal(focusCount, 1);
});
