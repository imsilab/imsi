# IMSI Teams and Alumni Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore live Team member photos and Alumni rendering despite the current malformed `WEB_People` header and shifted roster IDs.

**Architecture:** Add pure normalization and lookup functions to the shared sheet service, use them from `getPeople()` and the Teams page, and retain compatibility with a future correctly headed sheet. Prefer canonical profile routes from the existing author map, then category-derived routes, then initials.

**Tech Stack:** Vanilla JavaScript, Google Sheets gviz JSON, static HTML, Node.js test harness/Python `unittest`, Firefox WebDriver

**Spec:** `docs/superpowers/specs/2026-09-28-imsi-news-profiles-teams-design.md`

## Global Constraints

- Keep Teams and Alumni live from Google Sheets; do not introduce a static roster snapshot.
- Correctly formed future `WEB_People` data must pass through without destructive remapping.
- The observed pseudo-header row must not appear as a real person.
- Profile routes and avatars must prefer `data/author-profiles.json`.
- Render initials rather than broken images when no local or valid remote portrait is available.

## Review Focus

- A valid first person whose name resembles a header must not be dropped unless the full pseudo-header signature matches.
- IDs with more than one candidate must prefer exact canonical ID before shifted fallback.
- Empty names/categories and sparse rows must not create blank Alumni cards.
- Team members without profiles must remain visible with initials.
- Network failure must show the existing error state rather than throw an uncaught exception.

---

### Task 1: Define normalization and joining behavior with fixtures

**Files:**
- Create: `tests/test_people_sheet_normalization.py`
- Modify: `tests/test_browser_smoke.py`

**Interfaces:**
- Consumes: `normalizePeopleRows(rows)`, `createPeopleLookup(people)`, `resolveTeamPerson(membership, lookup)`
- Produces: executable malformed-header, valid-header, exact-ID, shifted-ID, sparse-row, and no-profile fixtures

- [ ] **Step 1: Write failing pure-function tests**

Use a Node `vm` harness from Python to load `js/SheetServices.js`. Assert that the observed `P_0001/Professor/Name_EN_FULL/...` row is removed, subsequent IDs normalize down by one, valid canonical rows retain their IDs, and exact lookup wins over shifted fallback.

- [ ] **Step 2: Run normalization tests and verify failure**

Run: `python3 -m unittest tests.test_people_sheet_normalization -v`

Expected: FAIL because the functions do not exist.

- [ ] **Step 3: Add failing browser assertions**

Load `/imsi/alumni/`, wait for both tabs, assert at least one Team member has a loaded local avatar, assert Alumni contains Youngung Han, and assert no pseudo-header person is rendered.

- [ ] **Step 4: Run the Teams browser test and verify failure**

Run: `python3 -m unittest tests.test_browser_smoke -v`

Expected: FAIL on missing photos/Alumni.

### Task 2: Implement shared people normalization

**Files:**
- Modify: `js/SheetServices.js`

**Interfaces:**
- Produces: `normalizePeopleRows(rows: Array<object>) -> Array<object>`
- Produces: `createPeopleLookup(people: Array<object>) -> {byId: Map, byShiftedId: Map, byName: Map}`
- Produces: `resolveTeamPerson(membership: object, lookup: object) -> object|null`
- Changes: `getPeople() -> Promise<Array<object>>` returns canonical person fields

- [ ] **Step 1: Implement pseudo-header detection and canonical reconstruction**

Detect the complete observed signature, drop only that row, map positional fields to `Person_ID`, `Category`, `Name_EN_FULL`, organization/contact/social/tag/photo fields, and decrement numeric IDs only for this malformed response shape.

- [ ] **Step 2: Implement resilient lookups**

Index exact IDs, original/shifted IDs, and normalized English names; resolve in that priority order.

- [ ] **Step 3: Preserve browser and Node compatibility**

Expose functions to `globalThis` and conditionally through `module.exports` without changing ordinary script loading.

- [ ] **Step 4: Run pure-function tests**

Run: `python3 -m unittest tests.test_people_sheet_normalization -v`

Expected: PASS.

### Task 3: Repair Teams/Alumni rendering and portraits

**Files:**
- Modify: `alumni/index.html`
- Modify: `tests/test_browser_smoke.py`

**Interfaces:**
- Consumes: normalized `getPeople()`, `getAuthorProfiles()`, `createPeopleLookup()`, `resolveTeamPerson()`
- Produces: populated Teams and Alumni tabs with internal profile/avatar routes

- [ ] **Step 1: Replace direct ID joins**

Build the shared lookup once and resolve every `WEB_PersonTeam` membership through `resolveTeamPerson()`.

- [ ] **Step 2: Prefer author-profile routes for links and portraits**

For mapped people, derive `avatar.png` from the canonical route; otherwise retain category-derived routing and initials fallback. Remove obsolete photo overrides where the map supersedes them.

- [ ] **Step 3: Normalize Alumni filtering**

Filter canonical `Category === "Alumni"`, ignore empty/pseudo-header rows, and render valid Alumni even when they have no team membership.

- [ ] **Step 4: Run Teams and full browser tests**

Run: `python3 -m unittest tests.test_people_sheet_normalization tests.test_browser_smoke -v`

Expected: PASS with live Team photos and visible Alumni.

- [ ] **Step 5: Commit**

Commit: `fix: restore Teams and Alumni roster rendering`

### Task 4: Integrated verification and publication

**Files:**
- Modify only if a failing assertion reveals an in-scope defect.

**Interfaces:**
- Consumes: all preceding news, profile, and Teams deliverables
- Produces: verified `main` branch pushed to existing origin

- [ ] **Step 1: Run the complete test suite**

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests PASS without skips other than unavailable optional browser tooling.

- [ ] **Step 2: Run repository checks**

Run: `python3 -m json.tool data/news-local.json >/dev/null && python3 -m json.tool data/author-profiles.json >/dev/null && git diff --check && git status --short`

Expected: valid JSON, clean diff check, and only intended changes before final commit.

- [ ] **Step 3: Review rendered routes**

Verify homepage, NEWS-005, NEWS-006, Minjun, Eunseob, Kyeonghun, Youngung, and Teams/Alumni under the local HTTP server at desktop and mobile viewport widths.

- [ ] **Step 4: Commit any final test-only integration changes**

Commit: `test: cover IMSI content and roster refresh`

- [ ] **Step 5: Confirm branch and push**

Run: `git status --short && git log --oneline --decorate -8 && git push origin main`

Expected: clean worktree and successful push to the existing `origin/main`.

