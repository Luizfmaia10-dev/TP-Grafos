const BH_BOUNDS = {
  north: -19.75,
  south: -20.05,
  east: -43.75,
  west: -44.1,
};

let autocompleteId = 0;

function insideBeloHorizonte(latitude, longitude) {
  return Number.isFinite(latitude) && Number.isFinite(longitude)
    && latitude <= BH_BOUNDS.north && latitude >= BH_BOUNDS.south
    && longitude <= BH_BOUNDS.east && longitude >= BH_BOUNDS.west;
}

export async function searchAddresses(
  apiKey,
  query,
  { fetchImpl = globalThis.fetch, signal } = {},
) {
  if (!apiKey) throw new Error("Geoapify API key is missing");
  const text = query.trim();
  if (text.length < 3) return [];
  const parameters = new URLSearchParams({
    text,
    format: "json",
    limit: "6",
    lang: "pt",
    filter: "rect:-44.1,-20.05,-43.75,-19.75",
    bias: "proximity:-43.94,-19.92",
    apiKey,
  });
  const response = await fetchImpl(
    `https://api.geoapify.com/v1/geocode/autocomplete?${parameters}`,
    { signal },
  );
  if (!response.ok) {
    throw new Error(`Geoapify request failed with status ${response.status}`);
  }
  const payload = await response.json();
  if (!Array.isArray(payload.results)) throw new Error("Invalid Geoapify response");
  return payload.results
    .filter(result => insideBeloHorizonte(Number(result.lat), Number(result.lon)))
    .map(result => ({
      label: result.formatted,
      latitude: Number(result.lat),
      longitude: Number(result.lon),
    }));
}

export function createAddressAutocomplete(
  apiKey,
  container,
  onSelect,
  onError = () => {},
  {
    documentRef = globalThis.document,
    fetchImpl = globalThis.fetch,
    delay = 300,
  } = {},
) {
  if (!apiKey) throw new Error("Geoapify API key is missing");
  const input = documentRef.createElement("input");
  const suggestions = documentRef.createElement("div");
  const listId = `address-suggestions-${autocompleteId += 1}`;
  let results = [];
  let activeIndex = -1;
  let timer = null;
  let controller = null;

  input.type = "search";
  input.className = "address-autocomplete-input";
  input.placeholder = "Digite um endereço de Belo Horizonte";
  input.autocomplete = "off";
  input.spellcheck = false;
  input.setAttribute("role", "combobox");
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-expanded", "false");
  input.setAttribute("aria-controls", listId);
  const labelledBy = container.getAttribute("aria-labelledby");
  if (labelledBy) input.setAttribute("aria-labelledby", labelledBy);

  suggestions.id = listId;
  suggestions.className = "address-suggestions";
  suggestions.setAttribute("role", "listbox");
  suggestions.hidden = true;

  function closeSuggestions() {
    suggestions.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    activeIndex = -1;
  }

  function select(result) {
    input.value = result.label;
    closeSuggestions();
    onSelect(result);
  }

  function renderSuggestions() {
    suggestions.replaceChildren(...results.map((result, index) => {
      const option = documentRef.createElement("button");
      option.type = "button";
      option.id = `${listId}-${index}`;
      option.className = "address-suggestion";
      option.textContent = result.label;
      option.setAttribute("role", "option");
      option.setAttribute("aria-selected", String(index === activeIndex));
      option.tabIndex = -1;
      option.addEventListener("mousedown", event => event.preventDefault());
      option.addEventListener("click", () => select(result));
      return option;
    }));
    suggestions.hidden = results.length === 0;
    input.setAttribute("aria-expanded", String(results.length > 0));
  }

  function moveActive(step) {
    if (results.length === 0) return;
    activeIndex = (activeIndex + step + results.length) % results.length;
    renderSuggestions();
    const active = suggestions.children[activeIndex];
    input.setAttribute("aria-activedescendant", active.id);
    active.scrollIntoView({ block: "nearest" });
  }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    controller?.abort();
    results = [];
    closeSuggestions();
    if (input.value.trim().length < 3) return;
    timer = setTimeout(async () => {
      controller = new AbortController();
      try {
        results = await searchAddresses(apiKey, input.value, {
          fetchImpl,
          signal: controller.signal,
        });
        renderSuggestions();
        if (results.length === 0) onError("Nenhum endereço encontrado em Belo Horizonte.");
      } catch (error) {
        if (error.name !== "AbortError") {
          onError("Não foi possível buscar endereços. Tente novamente.");
        }
      }
    }, delay);
  });

  input.addEventListener("keydown", event => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveActive(1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      moveActive(-1);
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      select(results[activeIndex]);
    } else if (event.key === "Escape") closeSuggestions();
  });
  input.addEventListener("blur", () => setTimeout(closeSuggestions, 100));

  container.replaceChildren(input, suggestions);
  delete container.dataset.unavailable;
  return input;
}
