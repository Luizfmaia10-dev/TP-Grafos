import assert from "node:assert/strict";
import test from "node:test";
import { createThemeSwitch, readStoredTheme, resolveInitialTheme, writeStoredTheme } from "../js/theme.js";

test("uses a valid stored theme before the system preference", () => {
  assert.equal(resolveInitialTheme("light", true), "light");
  assert.equal(resolveInitialTheme("dark", false), "dark");
});

test("falls back to the system preference", () => {
  assert.equal(resolveInitialTheme(null, true), "dark");
  assert.equal(resolveInitialTheme("invalid", false), "light");
});

test("storage failures do not block theme changes", () => {
  const unavailable = {
    getItem() { throw new Error("blocked"); },
    setItem() { throw new Error("blocked"); },
  };
  assert.equal(readStoredTheme(unavailable), null);
  assert.equal(writeStoredTheme(unavailable, "dark"), false);
});

test("persists the selected theme under one stable key", () => {
  const values = new Map();
  const storage = {
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  };
  assert.equal(writeStoredTheme(storage, "dark"), true);
  assert.equal(readStoredTheme(storage), "dark");
});

test("toggles the document state and accessible switch value", () => {
  const values = new Map();
  const attributes = new Map();
  const button = {
    dataset: {},
    setAttribute: (name, value) => attributes.set(name, value),
    addEventListener() {},
  };
  const browser = {
    localStorage: {
      getItem: key => values.get(key) ?? null,
      setItem: (key, value) => values.set(key, value),
    },
    matchMedia: () => ({ matches: false }),
  };
  const page = {
    documentElement: { dataset: {} },
    querySelector: () => null,
  };

  const controller = createThemeSwitch(button, browser, page);
  assert.equal(page.documentElement.dataset.theme, "light");
  assert.equal(attributes.get("aria-checked"), "false");
  controller.toggle();
  assert.equal(page.documentElement.dataset.theme, "dark");
  assert.equal(attributes.get("aria-checked"), "true");
  assert.equal(readStoredTheme(browser.localStorage), "dark");
});
