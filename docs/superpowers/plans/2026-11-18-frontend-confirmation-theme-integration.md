# Frontend Confirmation, Theme and Route Contract Implementation Plan

> Documento histórico: registra decisões e instruções da época, não tarefas abertas atuais. O progresso vigente está em [docs/PLAN.md](../../PLAN.md); contratos atuais em [API.md](../../API.md).

> **For Codex:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Add strict `HH:MM` departure input, origin-confirmation map motion, a project-native theme switch, a correct clear-field flow, and expose itinerary instructions through the existing route endpoint.

**Architecture:** Keep the local demo frontend and FastAPI domain boundaries unchanged. Put input-only transformations in small pure JavaScript functions, keep GTFS seconds internal to the backend, and reuse `Itinerary` as the single source of route presentation data. Use browser platform APIs with graceful reduced-motion fallbacks and no new runtime dependency.

**Tech Stack:** Python 3.13, FastAPI/Pydantic, pytest, HTML, Tailwind CSS 4, Vanilla JavaScript, Node test runner, Web Animations API, View Transitions API.

---

### Task 1: Enforce the minute-only API contract

**Files:**
- Modify: `backend/tests/test_routes_api.py`
- Modify: `backend/app/api/route_models.py`
- Modify: `backend/app/api/routes.py`
- Modify: `docs/API.md`

- [ ] Add failing API tests proving `HH:MM` is accepted, `HH:MM:SS` is rejected, and extended GTFS hours remain valid.
- [ ] Run the focused tests and confirm the expected RED result.
- [ ] Validate `departure_time` with a full `HH:MM` match at the request boundary.
- [ ] Append `:00` only when converting the request for `TimeUtils`.
- [ ] Run the focused tests and confirm GREEN.
- [ ] Document the public `HH:MM` contract without changing internal GTFS time precision.
- [ ] Commit in Portuguese with one clear responsibility.

### Task 2: Return itinerary instructions from the route endpoint

**Files:**
- Modify: `backend/tests/test_routes_api.py`
- Modify: `backend/app/api/route_models.py`
- Modify: `backend/app/api/routes.py`
- Modify: `docs/API.md`

- [ ] Add failing response tests for `instructions` on found and empty routes.
- [ ] Run the focused tests and confirm the expected RED result.
- [ ] Add `instructions` to `RouteResult` and copy the already-calculated list from `Itinerary`.
- [ ] Run the focused tests and confirm GREEN.
- [ ] Correct stale API documentation that says `Itinerary` is absent.
- [ ] Commit in Portuguese with one clear responsibility.

### Task 3: Mask and validate the frontend departure time

**Files:**
- Create: `frontend/js/time-mask.js`
- Create: `frontend/tests/time-mask.test.js`
- Modify: `frontend/js/selection.js`
- Modify: `frontend/tests/selection.test.js`
- Modify: `frontend/js/demo-service.js`
- Modify: `frontend/index.html`
- Modify: `frontend/js/app.js`

- [ ] Add failing pure-function tests for digit entry, formatted entry, deletion, extended hours, invalid minutes, and removal of seconds.
- [ ] Update selection tests so normalization returns only `HH:MM` and rejects seconds.
- [ ] Run focused frontend tests and confirm RED.
- [ ] Implement the smallest pure mask and strict `HH:MM` normalization.
- [ ] Convert minutes to internal seconds only inside the demo service.
- [ ] Wire the mask to a numeric text input without using `type=time`.
- [ ] Run focused tests and confirm GREEN.
- [ ] Commit in Portuguese with one clear responsibility.

### Task 4: Correct clear behavior and confirm origin on field exit

**Files:**
- Create: `frontend/js/origin-confirmation.js`
- Create: `frontend/tests/origin-confirmation.test.js`
- Modify: `frontend/js/app.js`
- Modify: `frontend/js/map.js`
- Modify: `frontend/tests/map.test.js`
- Modify: `frontend/index.html`

- [ ] Add failing tests for one confirmation per selected origin and reset after edit or clear.
- [ ] Run focused frontend tests and confirm RED.
- [ ] Stop the clear handler from reopening suggestions while preserving focus and cancellation.
- [ ] Detect focus leaving the entire origin field and confirm only a selected station.
- [ ] Add a map method that animates the matching marker and panel, scrolls only on small viewports, and respects reduced motion.
- [ ] Announce the confirmed station through the existing status region.
- [ ] Run focused tests and confirm GREEN.
- [ ] Commit in Portuguese with one clear responsibility.

### Task 5: Add the project-native theme switch

**Files:**
- Create: `frontend/js/theme.js`
- Create: `frontend/tests/theme.test.js`
- Modify: `frontend/index.html`
- Modify: `frontend/js/app.js`
- Modify: `frontend/styles/app.css`
- Modify: `frontend/assets/app.css`

- [ ] Add failing tests for stored preference, system fallback, toggle state, and unavailable storage.
- [ ] Run focused frontend tests and confirm RED.
- [ ] Add an accessible switch in the header and persist `light`/`dark` on `<html>`.
- [ ] Add flat project-colour tokens for both themes, with a 44px target and visible focus.
- [ ] Reveal the theme from the switch with View Transitions when available; otherwise change immediately.
- [ ] Add reduced-motion behavior and compile the Tailwind asset.
- [ ] Run focused tests and confirm GREEN.
- [ ] Commit in Portuguese with one clear responsibility.

### Task 6: Integrate styles, documentation and progress

**Files:**
- Modify: `frontend/styles/app.css`
- Modify: `frontend/assets/app.css`
- Modify: `frontend/README.md`
- Modify: `docs/PLAN.md`

- [ ] Style the confirmation state with transform, opacity and clip-path only; avoid gradients, glows and layout animation.
- [ ] Keep light mode visually compatible and make dark surfaces neutral enough for legibility while retaining the system accent colours.
- [ ] Document the mask, clear behavior, theme control and origin confirmation.
- [ ] Mark only genuinely completed checkboxes in `docs/PLAN.md`, preserving item text.
- [ ] Rebuild CSS and run the design lint for the changed app screen.
- [ ] Commit in Portuguese with one clear responsibility.

### Task 7: Verify the complete delivery

**Files:**
- Test: `backend/tests/`
- Test: `frontend/tests/`

- [ ] Run the full Python suite.
- [ ] Run the full frontend suite.
- [ ] Run the production CSS build and ensure the working tree stays clean except expected generated changes.
- [ ] Start the application and verify route resources over HTTP.
- [ ] Inspect the app at phone, tablet and desktop widths; check keyboard focus and reduced motion.
- [ ] Review the final diff for unnecessary code and regressions.
- [ ] Commit any verification-only documentation adjustment separately.
