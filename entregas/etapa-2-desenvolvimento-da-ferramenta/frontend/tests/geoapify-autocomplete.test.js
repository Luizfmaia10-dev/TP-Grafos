import assert from "node:assert/strict";
import test from "node:test";
import { searchAddresses } from "../js/geoapify-autocomplete.js";

test("Geoapify autocomplete restricts results to Belo Horizonte", async () => {
  let requestedUrl;
  const results = await searchAddresses("browser-key", "Rua da Bahia", {
    fetchImpl: async url => {
      requestedUrl = new URL(url);
      return Response.json({ results: [
        { formatted: "Rua da Bahia, Belo Horizonte - MG", lat: -19.92, lon: -43.94 },
        { formatted: "Rua da Bahia, Contagem - MG", lat: -19.93, lon: -44.2 },
      ] });
    },
  });

  assert.equal(requestedUrl.hostname, "api.geoapify.com");
  assert.equal(requestedUrl.pathname, "/v1/geocode/autocomplete");
  assert.equal(requestedUrl.searchParams.get("filter"), "rect:-44.1,-20.05,-43.75,-19.75");
  assert.equal(requestedUrl.searchParams.get("bias"), "proximity:-43.94,-19.92");
  assert.equal(requestedUrl.searchParams.get("apiKey"), "browser-key");
  assert.deepEqual(results, [{
    label: "Rua da Bahia, Belo Horizonte - MG",
    latitude: -19.92,
    longitude: -43.94,
  }]);
});

test("Geoapify autocomplete waits for three characters", async () => {
  let requests = 0;
  const results = await searchAddresses("browser-key", "Ru", {
    fetchImpl: async () => { requests += 1; },
  });

  assert.deepEqual(results, []);
  assert.equal(requests, 0);
});

test("Geoapify autocomplete reports denied requests", async () => {
  await assert.rejects(
    searchAddresses("browser-key", "Avenida", {
      fetchImpl: async () => new Response(null, { status: 429 }),
    }),
    /Geoapify request failed with status 429/,
  );
});
