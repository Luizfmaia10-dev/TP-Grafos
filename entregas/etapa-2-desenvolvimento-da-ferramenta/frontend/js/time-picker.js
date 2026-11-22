export function parsePickerTime(value) {
  const match = /^(\d{2,}):([0-5]\d)$/.exec(value);
  return match ? { hour: Number(match[1]), minute: Number(match[2]) } : null;
}

export function formatPickerTime(hour, minute) {
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

export function createWheelValues(max) {
  return Array.from({ length: max + 1 }, (_, value) => String(value).padStart(2, "0"));
}

export function stepWheelValue(value, step, max) {
  return (value + step + max + 1) % (max + 1);
}

export function createTimePicker(root, input, trigger) {
  const hourWheel = root.querySelector('[data-wheel="hour"]');
  const minuteWheel = root.querySelector('[data-wheel="minute"]');
  const applyButton = root.querySelector('[data-time-apply]');
  const cancelButton = root.querySelector('[data-time-cancel]');
  let selected = parsePickerTime(input.value) ?? { hour: 7, minute: 45 };
  let scrollTimer = null;

  const wheels = {
    hour: { element: hourWheel, max: 47 },
    minute: { element: minuteWheel, max: 59 },
  };

  function select(kind, value, behavior = "smooth") {
    selected = { ...selected, [kind]: value };
    const wheel = wheels[kind].element;
    for (const option of wheel.children) {
      const isSelected = Number(option.dataset.value) === value;
      option.setAttribute("aria-selected", String(isSelected));
      option.dataset.selected = String(isSelected);
      if (isSelected) option.scrollIntoView({ block: "center", behavior });
    }
  }

  function populate(kind, max) {
    const wheel = wheels[kind].element;
    const options = createWheelValues(max).map(value => {
      const option = document.createElement("button");
      option.type = "button";
      option.className = "time-wheel-option";
      option.dataset.value = value;
      option.setAttribute("role", "option");
      option.setAttribute("aria-label", kind === "hour" ? `${Number(value)} horas` : `${Number(value)} minutos`);
      option.textContent = value;
      option.tabIndex = -1;
      option.addEventListener("click", () => select(kind, Number(value)));
      return option;
    });
    wheel.replaceChildren(...options);
  }

  function open() {
    selected = parsePickerTime(input.value) ?? { hour: 7, minute: 45 };
    wheels.hour.max = Math.max(47, selected.hour);
    populate("hour", wheels.hour.max);
    populate("minute", wheels.minute.max);
    root.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
    requestAnimationFrame(() => {
      select("hour", selected.hour, "instant");
      select("minute", selected.minute, "instant");
      hourWheel.focus({ preventScroll: true });
    });
  }

  function close({ restoreFocus = true } = {}) {
    if (root.hidden) return;
    root.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
    if (restoreFocus) trigger.focus({ preventScroll: true });
  }

  function step(kind, amount) {
    const wheel = wheels[kind];
    select(kind, stepWheelValue(selected[kind], amount, wheel.max));
  }

  for (const [kind, wheel] of Object.entries(wheels)) {
    wheel.element.addEventListener("keydown", event => {
      const steps = { ArrowUp: -1, ArrowDown: 1, PageUp: -5, PageDown: 5 };
      if (event.key === "Home" || event.key === "End") {
        event.preventDefault();
        select(kind, event.key === "Home" ? 0 : wheel.max);
      } else if (event.key in steps) {
        event.preventDefault();
        step(kind, steps[event.key]);
      }
    });
    wheel.element.addEventListener("scroll", () => {
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(() => {
        const center = wheel.element.getBoundingClientRect().top + wheel.element.clientHeight / 2;
        const closest = [...wheel.element.children].reduce((best, option) => {
          const rect = option.getBoundingClientRect();
          const distance = Math.abs(rect.top + rect.height / 2 - center);
          return !best || distance < best.distance ? { option, distance } : best;
        }, null);
        if (closest) select(kind, Number(closest.option.dataset.value), "instant");
      }, 100);
    }, { passive: true });
  }

  trigger.addEventListener("click", () => root.hidden ? open() : close());
  cancelButton.addEventListener("click", () => close());
  applyButton.addEventListener("click", () => {
    input.value = formatPickerTime(selected.hour, selected.minute);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    close();
  });
  root.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      event.preventDefault();
      close();
    }
  });
  document.addEventListener("pointerdown", event => {
    if (!root.hidden && !root.contains(event.target) && !trigger.contains(event.target)) {
      close({ restoreFocus: false });
    }
  });

  return { open, close };
}
