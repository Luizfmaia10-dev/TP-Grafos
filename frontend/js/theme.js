const THEME_KEY = "rotasgraph-theme";

export function resolveInitialTheme(storedTheme, prefersDark) {
  if (storedTheme === "light" || storedTheme === "dark") return storedTheme;
  return prefersDark ? "dark" : "light";
}

export function readStoredTheme(storage) {
  try {
    return storage.getItem(THEME_KEY);
  } catch {
    return null;
  }
}

export function writeStoredTheme(storage, theme) {
  try {
    storage.setItem(THEME_KEY, theme);
    return true;
  } catch {
    return false;
  }
}

export function createThemeSwitch(button, browser = window, page = document) {
  const media = browser.matchMedia("(prefers-color-scheme: dark)");
  let theme = resolveInitialTheme(readStoredTheme(browser.localStorage), media.matches);

  function apply(nextTheme) {
    theme = nextTheme;
    page.documentElement.dataset.theme = theme;
    button.setAttribute("aria-checked", String(theme === "dark"));
    button.dataset.theme = theme;
    page.querySelector('meta[name="theme-color"]')?.setAttribute(
      "content", theme === "dark" ? "#07111d" : "#032147",
    );
  }

  function toggle() {
    const nextTheme = theme === "dark" ? "light" : "dark";
    writeStoredTheme(browser.localStorage, nextTheme);
    const reduceMotion = browser.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion || typeof page.startViewTransition !== "function") {
      apply(nextTheme);
      return;
    }
    const bounds = button.getBoundingClientRect();
    const x = bounds.left + bounds.width / 2;
    const y = bounds.top + bounds.height / 2;
    const radius = Math.hypot(Math.max(x, browser.innerWidth - x), Math.max(y, browser.innerHeight - y));
    const transition = page.startViewTransition(() => apply(nextTheme));
    transition.ready.then(() => page.documentElement.animate(
      { clipPath: [`circle(0 at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
      { duration: 420, easing: "cubic-bezier(0.16, 1, 0.3, 1)", pseudoElement: "::view-transition-new(root)" },
    )).catch(() => {});
  }

  apply(theme);
  button.addEventListener("click", toggle);
  return { get theme() { return theme; }, toggle };
}
