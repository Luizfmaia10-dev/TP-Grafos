import assert from "node:assert/strict";
import test from "node:test";
import { ApiError } from "../js/api-service.js";
import { createRouteRequest } from "../js/route-request.js";

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

test("a request reports loading and then its result", async () => {
  const operation = deferred();
  const states = [];
  const request = createRouteRequest(() => operation.promise, state => states.push(state.status));
  const pending = request.submit({ departureTime: "07:45:00" });
  assert.equal(request.state.status, "loading");
  operation.resolve({ status: "found" });
  await pending;
  assert.deepEqual(states, ["loading", "found"]);
});

test("repeated submissions cannot start simultaneous searches", async () => {
  const operation = deferred();
  let calls = 0;
  const request = createRouteRequest(() => { calls++; return operation.promise; }, () => {});
  const pending = request.submit({});
  await request.submit({});
  assert.equal(calls, 1);
  operation.resolve({ status: "no-route" });
  await pending;
  assert.equal(request.state.status, "no-route");
});

test("editing cancels the signal and ignores a late response, even if the service ignores abort", async () => {
  const operation = deferred();
  let signal;
  const request = createRouteRequest((query, options) => {
    signal = options.signal;
    return operation.promise;
  }, () => {});
  const pending = request.submit({});
  request.cancel();
  assert.equal(signal.aborted, true);
  operation.resolve({ status: "found" });
  await pending;
  assert.equal(request.state.status, "idle");
});

test("an older query cannot overwrite a newer query", async () => {
  const old = deferred();
  const recent = deferred();
  const request = createRouteRequest(query => query.id === 1 ? old.promise : recent.promise, () => {});
  const first = request.submit({ id: 1 });
  request.cancel();
  const second = request.submit({ id: 2 });
  recent.resolve({ status: "no-route" });
  await second;
  old.resolve({ status: "found" });
  await first;
  assert.equal(request.state.status, "no-route");
});

test("a failed request can be retried", async () => {
  let calls = 0;
  const request = createRouteRequest(async () => {
    if (++calls === 1) throw new Error("Test failure");
    return { status: "found" };
  }, () => {});
  await request.submit({});
  assert.equal(request.state.status, "error");
  await request.submit({});
  assert.equal(request.state.status, "found");
});

test("a failed request preserves the error in its published state", async () => {
  const failure = new ApiError("unavailable", 503, "unavailable");
  const states = [];
  const request = createRouteRequest(async () => { throw failure; }, state => states.push(state));

  await request.submit({});

  assert.equal(request.state.error, failure);
  assert.deepEqual(states, [{ status: "loading" }, { status: "error", error: failure }]);
});

test("a rejected cancelled query cannot turn into a visible error", async () => {
  const operation = deferred();
  const request = createRouteRequest(() => operation.promise, () => {});
  const pending = request.submit({});
  request.cancel();
  operation.reject(new Error("Late failure"));
  await pending;
  assert.equal(request.state.status, "idle");
});
