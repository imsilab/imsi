# IMSI News Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the corrected 2027 undergraduate interview announcement and internally linked NeurIPS 2026 acceptance news.

**Architecture:** Keep local priority news in `data/news-local.json`, which is already merged with Google Sheet news by `getNews()`. Exercise the rendered Markdown through the existing dynamic detail pages and browser smoke tests.

**Tech Stack:** Static HTML, JSON, JavaScript/Marked, Python `unittest`, Firefox WebDriver

**Spec:** `docs/superpowers/specs/2026-09-28-imsi-news-profiles-teams-design.md`

## Global Constraints

- Preserve the existing Google Sheet plus local-news merge.
- Do not include access codes.
- Internal author links stay within `/imsi/`; external links open safely in a new tab through the existing Markdown renderer.
- Use exact publication counts supplied in the spec.

## Review Focus

- Markdown author links must render as four distinct internal anchors, not plain text.
- The Nam-Joon Kim dagger must be absent from both source JSON and rendered news.
- Institutional names and conference counts must not be silently altered by punctuation or Markdown parsing.
- The IMSI introduction URL must use the exact requested `http://capp.snu.ac.kr/imsi/` value.
- Existing sheet news and both local news items must remain visible after merging.

---

### Task 1: Pin the requested news content

**Files:**
- Modify: `tests/test_requested_site_content.py`
- Modify: `tests/test_browser_smoke.py`

**Interfaces:**
- Consumes: `data/news-local.json` records keyed by `News_ID`
- Produces: assertions covering the complete NEWS_005 and NEWS_006 contract

- [ ] **Step 1: Write failing source-content tests**

Add assertions for the exact IMSI URL, all four exchange dates, all eleven visited institutions, every requested publication count, all four author profile routes, and absence of `Nam-Joon Kim†`.

- [ ] **Step 2: Run the focused test and verify failure**

Run: `python3 -m unittest tests.test_requested_site_content.RequestedSiteContentTests.test_news_detail_pages_have_required_content_and_no_access_codes -v`

Expected: FAIL on the old URL/content and missing author anchors.

- [ ] **Step 3: Write failing browser assertions**

Extend the two news detail checks to return rendered anchor paths and verify the IMSI link plus the four author routes.

- [ ] **Step 4: Run the focused browser test and verify failure**

Run: `python3 -m unittest tests.test_browser_smoke.BrowserSmokeTests.test_sheet_and_local_news_merge_and_render_across_routes -v`

Expected: FAIL because the current rendered content lacks the required links.

### Task 2: Update both local news records

**Files:**
- Modify: `data/news-local.json`

**Interfaces:**
- Consumes: the existing `getNews() -> Promise<Array<Record<string,string>>>` merge
- Produces: Markdown content rendered by `/imsi/news/NEWS-005/` and `/imsi/news/NEWS-006/`

- [ ] **Step 1: Update NEWS_005**

Replace the author line with four Markdown links to the canonical IMSI profiles and remove the dagger.

- [ ] **Step 2: Update NEWS_006**

Use the exact IMSI URL, requested activity dates, a concise “Institutional Visits & Collaboration” section, and exact publication output counts while retaining the no-access-code wording.

- [ ] **Step 3: Run source and browser tests**

Run: `python3 -m unittest tests.test_requested_site_content tests.test_browser_smoke.BrowserSmokeTests.test_sheet_and_local_news_merge_and_render_across_routes -v`

Expected: PASS.

- [ ] **Step 4: Validate JSON and commit**

Run: `python3 -m json.tool data/news-local.json >/dev/null && git diff --check`

Expected: exit 0.

Commit: `feat: refresh IMSI news announcements`

