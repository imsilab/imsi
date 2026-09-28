# IMSI Profile Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Minjun Yoo and enrich the Eunseob Choi, Kyeonghun Kim, and Youngung Han profiles with consistent verified highlights and assets.

**Architecture:** Follow the existing hand-authored Academic-theme profile pattern, reuse publication filtering and Fancybox, and register canonical internal routes in `data/author-profiles.json`. Normalize supplied images into profile-local web assets.

**Tech Stack:** Static HTML/CSS, JavaScript, Pillow/ImageMagick if available, Fancybox, Python `unittest`, Firefox WebDriver

**Spec:** `docs/superpowers/specs/2026-09-28-imsi-news-profiles-teams-design.md`

## Global Constraints

- Preserve all automatic publication lists.
- Use verified official external links and safe `target="_blank" rel="noopener"` attributes.
- Present the supplied dates and future venue counts as supplied; do not add unverified patent metadata.
- Keep profile styling consistent with the existing site and place both ORCID icons identically.
- Do not expose the supplied Git token in files, logs, or remotes.

## Review Focus

- Missing image processing tools must not result in mislabeled file extensions; verify actual PNG signatures and dimensions.
- A missing exact KBS segment must not be replaced with a fabricated deep link.
- Minjun must appear exactly once and immediately before Giseong Hwang.
- Fancybox thumbnails must open local full-resolution award images without broken relative paths.
- Existing filtered publication loaders and profile scripts must still execute after new markup is inserted.

---

### Task 1: Pin profile and asset requirements

**Files:**
- Modify: `tests/test_requested_site_content.py`
- Modify: `tests/test_browser_smoke.py`

**Interfaces:**
- Consumes: static profile HTML, `data/author-profiles.json`, local PNG/JPEG assets
- Produces: profile content, ordering, link, image, and runtime assertions

- [ ] **Step 1: Write failing static tests**

Add tests for the seven-person intern order, Minjun's canonical route and supplied data, official app/media links, two news highlight cards, both ORCID URLs, Kyeonghun's requested research counts, patent number, teaching/volunteering entries, and both donation image paths.

- [ ] **Step 2: Run static tests and verify failure**

Run: `python3 -m unittest tests.test_requested_site_content -v`

Expected: FAIL because the new profile and content do not exist.

- [ ] **Step 3: Write failing browser tests**

Add navigation checks for Minjun's portrait and links, both NeurIPS cards, Kyeonghun's ORCID and donation lightbox anchors, and Youngung's ORCID.

- [ ] **Step 4: Run focused browser tests and verify failure**

Run: `python3 -m unittest tests.test_browser_smoke -v`

Expected: FAIL on the missing profile/content.

### Task 2: Create Minjun Yoo's profile and homepage card

**Files:**
- Create: `authors/undergraduate_interns/minjun-yoo/index.html`
- Create: `authors/undergraduate_interns/minjun-yoo/avatar.png`
- Modify: `index.html`
- Modify: `data/author-profiles.json`

**Interfaces:**
- Consumes: source image `../temp_cdx/imgs/minjun-yoo.png`
- Produces: canonical route `/imsi/authors/undergraduate_interns/minjun-yoo/`

- [ ] **Step 1: Normalize the portrait**

Create a square, web-sized PNG from the supplied source, preserving recognizable content and verifying its PNG signature.

- [ ] **Step 2: Build the profile**

Include email, education dates, Mathematics Education, Geuneulro description, Instagram, Google Play, Apple App Store, recruitment, official tvN, and official SBS links. Mention KBS only with a verified official reference or clearly without a fabricated deep link.

- [ ] **Step 3: Add homepage ordering and profile mapping**

Insert the card immediately before Giseong Hwang and add `"Minjun Yoo": "/imsi/authors/undergraduate_interns/minjun-yoo/"`.

- [ ] **Step 4: Run focused tests**

Run: `python3 -m unittest tests.test_requested_site_content.RequestedSiteContentTests.test_undergraduate_interns_have_exact_requested_order tests.test_browser_smoke.BrowserSmokeTests.test_people_order_and_yului_profile_render -v`

Expected: PASS after updating the browser's expected order and Minjun checks.

- [ ] **Step 5: Commit**

Commit: `feat: add Minjun Yoo profile`

### Task 3: Add NeurIPS and ORCID profile highlights

**Files:**
- Modify: `authors/undergraduate_interns/eunseob-choi/index.html`
- Modify: `authors/research_assistants/kyeonghun-kim/index.html`
- Modify: `authors/research_assistants/youngung-han/index.html`

**Interfaces:**
- Consumes: `/imsi/news/NEWS-005/`, ORCID identifiers
- Produces: consistent highlight cards and portrait-adjacent ORCID anchors

- [ ] **Step 1: Add two NeurIPS cards**

Use a compact, high-contrast “Research Highlight” card on Eunseob and Kyeonghun that links internally to NEWS-005.

- [ ] **Step 2: Add matching ORCID icons**

Link Kyeonghun to `https://orcid.org/0009-0002-9405-8424` and Youngung to `https://orcid.org/0009-0008-0596-8367` at the same position in each network icon list.

- [ ] **Step 3: Run profile tests**

Run: `python3 -m unittest tests.test_requested_site_content tests.test_browser_smoke -v`

Expected: all highlight and ORCID assertions PASS.

- [ ] **Step 4: Commit**

Commit: `feat: add profile research highlights`

### Task 4: Expand Kyeonghun Kim's research, patent, teaching, and service record

**Files:**
- Modify: `authors/research_assistants/kyeonghun-kim/index.html`
- Create: `authors/research_assistants/kyeonghun-kim/blood-donation-silver.png`
- Create: `authors/research_assistants/kyeonghun-kim/blood-donation-gold.png`

**Interfaces:**
- Consumes: source images in `../temp_cdx/imgs/blood_donations/`, existing Fancybox dependency
- Produces: scannable English profile sections and two `data-fancybox="blood-donation-awards"` anchors

- [ ] **Step 1: Normalize award images**

Convert both supplied images to readable PNG assets with bounded web dimensions while retaining enough resolution for lightbox inspection.

- [ ] **Step 2: Rewrite the biography and research highlights**

Add the verified 3D-LLDM first-author/ISBI oral description, Stanford/NVIDIA/SMC collaboration, Silicon Valley tour, and exact venue-count summary.

- [ ] **Step 3: Add patent, teaching, and volunteering sections**

Use the supplied patent title and number with a KIPRIS search link; add the requested teaching engagements; summarize 50+ blood donations since 2018, Silver/Gold dates, Korean Red Cross link, and NAVER Happy Bean recurring giving with NAVER Corp link.

- [ ] **Step 4: Add the award lightbox gallery**

Render compact thumbnails linking to the normalized full images through the existing Fancybox group.

- [ ] **Step 5: Run profile tests and asset checks**

Run: `python3 -m unittest tests.test_requested_site_content tests.test_browser_smoke -v && file authors/research_assistants/kyeonghun-kim/blood-donation-*.png && git diff --check`

Expected: tests PASS; `file` reports PNG images; diff check exits 0.

- [ ] **Step 6: Commit**

Commit: `feat: expand Kyeonghun Kim profile`

