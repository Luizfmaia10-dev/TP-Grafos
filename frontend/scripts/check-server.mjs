import assert from "node:assert/strict";
import test from "node:test";
import { extname } from "node:path";

const base = new URL(process.env.FRONTEND_BASE_URL ?? "http://127.0.0.1:8000");
const contentTypes = {
  ".css": ["text/css"],
  ".js": ["text/javascript", "application/javascript"],
  ".svg": ["image/svg+xml"],
  ".woff2": ["font/woff2"],
};

async function request(url) {
  try {
    return await fetch(url, { signal: AbortSignal.timeout(5000), redirect: "error" });
  } catch (cause) {
    throw new Error(`Cannot reach ${url}. Start FastAPI or set FRONTEND_BASE_URL.`, { cause });
  }
}

function htmlResources(html) {
  const references = [];
  for (const [tag] of html.matchAll(/<(?:script|img|link)\b[^>]*>/giu)) {
    const match = tag.match(/\b(?:src|href)=["']([^"']+)["']/u);
    if (match) references.push(match[1]);
  }
  return references;
}

function moduleResources(source) {
  return [
    ...source.matchAll(/\bfrom\s+["']([^"']+)["']/gu),
    ...source.matchAll(/\bimport\s+["']([^"']+)["']/gu),
    ...source.matchAll(/\.src\s*=\s*["']([^"']+)["']/gu),
  ].map(match => match[1]);
}

test("FastAPI serves the frontend and its local dependency graph", { timeout: 60000 }, async t => {
  const health = await request(new URL("/health", base));
  await t.test("health endpoint remains available before the static mount", async () => {
    assert.equal(health.status, 200);
    assert.match(health.headers.get("content-type"), /application\/json/u);
    assert.deepEqual(await health.json(), { status: "ok" });
  });

  const entry = await request(new URL("/", base));
  const html = await entry.text();
  await t.test("entry page is HTML and loads the native JavaScript module", () => {
    assert.equal(entry.status, 200);
    assert.match(entry.headers.get("content-type"), /^text\/html\b/u);
    assert.match(html, /<html\b/iu);
    assert.match(html, /<script\b[^>]*type=["']module["'][^>]*src=["'][^"']+["']/iu);
    assert.ok(htmlResources(html).length > 0);
  });

  const pending = htmlResources(html).map(reference => new URL(reference, entry.url));
  const visited = new Set();
  for (let index = 0; index < pending.length; index++) {
    const url = pending[index];
    if (visited.has(url.href)) continue;
    visited.add(url.href);
    await t.test(`resource ${url.pathname}`, async () => {
      assert.equal(url.origin, base.origin, "Demonstration assets must be local");
      const extension = extname(url.pathname);
      assert.ok(contentTypes[extension], `Unexpected asset type: ${url.pathname}`);
      const response = await request(url);
      assert.equal(response.status, 200, `Missing resource: ${url.pathname}`);
      const contentType = response.headers.get("content-type")?.split(";")[0];
      assert.ok(contentTypes[extension].includes(contentType), `Unexpected content type ${contentType}`);
      const bytes = new Uint8Array(await response.arrayBuffer());
      assert.ok(bytes.length > 0, "Resources must not be empty");
      if (extension === ".woff2") {
        assert.equal(new TextDecoder().decode(bytes.slice(0, 4)), "wOF2");
        return;
      }
      const source = new TextDecoder().decode(bytes);
      assert.doesNotMatch(source.trimStart(), /^<(?:!doctype\s+html|html)\b/iu, "An asset returned HTML");
      if (extension === ".svg") assert.match(source, /<svg\b/u);
      if (extension === ".css") {
        for (const match of source.matchAll(/url\(["']?([^"')]+)["']?\)/gu)) {
          pending.push(new URL(match[1], response.url));
        }
      }
      if (extension === ".js") {
        pending.push(...moduleResources(source).map(reference => new URL(reference, response.url)));
      }
    });
  }
  t.diagnostic(`${visited.size} distinct asset URLs checked`);

  for (const pathname of ["/assets/missing-check.css", "/js/missing-check.js", "/assets/maps/missing-check.svg"]) {
    await t.test(`unknown asset ${pathname} is a 404 rather than the entry page`, async () => {
      const response = await request(new URL(pathname, base));
      assert.equal(response.status, 404);
      assert.doesNotMatch(response.headers.get("content-type") ?? "", /text\/html/u);
    });
  }
});
