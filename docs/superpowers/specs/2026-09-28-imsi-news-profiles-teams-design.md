# IMSI News, Profiles, and Teams Refresh Design

## Goal

Refresh the IMSI Lab site with the requested October 2026 interview announcement, NeurIPS news links, Minjun Yoo profile, expanded researcher profiles, and reliable Teams/Alumni rendering while preserving the site's current static HTML and Google Sheets integration.

## Scope

### News

- Update `NEWS_006` in `data/news-local.json`.
- Point the IMSI introduction link to `http://capp.snu.ac.kr/imsi/`.
- Add the four requested domestic and international exchange activities.
- Add a concise section covering institutional visits and collaboration meetings at KBS, NVIDIA Korea, NVIDIA Singapore, NVIDIA San Jose, Google, Salesforce, Uber, Microsoft, Stanford University, UC Berkeley, and Samsung Medical Center. Do not attribute this section to a named leader.
- Replace the current publication summary with exact requested counts: two MICCAI Workshop papers, three ISBI oral papers, two NeurIPS 2026 papers, one CVPR paper, one IEEE MedAI paper, four AICAS papers, four APCCAS papers, five GTC posters, and one AAAI Workshop paper.
- Update `NEWS_005` by removing the dagger after Nam-Joon Kim and linking all four authors to their internal IMSI profile pages.

### Minjun Yoo

- Create `authors/undergraduate_interns/minjun-yoo/` with `index.html` and a normalized `avatar.png` derived from the supplied source image.
- Add Minjun immediately before Giseong Hwang in the homepage Undergraduate Interns section.
- Add Minjun to the internal author-profile map so internal links resolve consistently.
- Present the supplied education dates as March 2023 to March 2028 (expected), with Seoul National University Mathematics Education, class of 2023, and current second-year status.
- Describe Geuneulro as a public-data-based shade-aware navigation application and link its Instagram, Android, iOS, and recruitment pages.
- Link only verified direct media sources. Use the official tvN episode/video page for *You Quiz on the Block*, the official SBS report, and an official KBS page if an exact segment can be verified. If no exact KBS segment is discoverable, mention the appearance without inventing a deep link and link the broadcaster or an official search result clearly labelled as such.

### Researcher Profiles

- Add a compact NeurIPS 2026 highlight card to Eunseob Choi and Kyeonghun Kim, linking to `/imsi/news/NEWS-005/`.
- Expand Kyeonghun Kim's profile in polished English with:
  - first-author 3D-LLDM work and its ISBI 2026 oral presentation;
  - collaborations involving Stanford, NVIDIA, and Samsung Medical Center;
  - the Silicon Valley company visit programme;
  - the requested venue-count summary;
  - patent information supplied by the user, with a conservative KIPRIS search link unless an exact authoritative patent detail page is verified;
  - concise teaching experience;
  - concise volunteering entries for Korean Red Cross blood donation and NAVER Happy Bean recurring giving;
  - two blood-donation award images displayed as thumbnails that open in the existing Fancybox lightbox.
- Add ORCID links beside the portrait/social links for Kyeonghun Kim (`0009-0002-9405-8424`) and Youngung Han (`0009-0008-0596-8367`) using the same visual placement.
- Convert blood-donation images to a consistent web format and retain legibility in the lightbox.
- Keep automatically filtered publication lists intact.

### Teams and Alumni

The current Google Sheets response for `WEB_People` is malformed for the generic parser: its first person row is interpreted as the header. The resulting objects lack canonical fields such as `Person_ID` and `Category`. In addition, IDs in `WEB_PersonTeam` are shifted relative to `WEB_People`, so direct joins fail.

Implement a normalization layer in `js/SheetServices.js` (or a narrowly scoped shared helper used by the Teams page) that:

1. Detects the malformed `WEB_People` shape without altering correctly formed future responses.
2. Reconstructs canonical person fields from the parser's positional `Column_n` values and the captured first-row values.
3. Normalizes category/role values used for profile routes and Alumni filtering.
4. Resolves team membership primarily by canonical person ID, with a deterministic fallback for the observed one-position ID shift and, where possible, a normalized-name fallback.
5. Uses `data/author-profiles.json` as the preferred source for internal profile/avatar routes and falls back to category-derived paths or initials.
6. Leaves future valid sheet rows dynamic rather than replacing the sheet with a static snapshot.

## Presentation

- Reuse the existing Academic-theme typography, spacing, cards, social icons, and Fancybox dependency.
- Use short, scannable sections rather than a single long biography.
- Use consistent labels across profiles: Research Highlights, Publications, Teaching Experience, Volunteering, and selected personal or project highlights only where relevant.
- Ensure external links open safely in a new tab and internal IMSI links remain in-site.

## Data and Accuracy Rules

- User-supplied future conference counts and personal dates may be presented as supplied.
- Do not fabricate publication, patent, media, or app URLs.
- For external claims with discoverable primary sources, prefer conference programmes, paper records, broadcaster pages, app stores, institutional sites, and ORCID.
- Preserve live spreadsheet publication filtering already used by individual profiles.

## Verification

- Extend the existing Python content tests to cover requested text, ordering, URLs, profile mapping, ORCID links, news author links, lightbox assets, and no dagger in the NeurIPS author line.
- Add unit-level fixtures for both malformed and well-formed `WEB_People` data and shifted team IDs.
- Run browser smoke tests against a local HTTP server for the homepage, both news pages, Minjun Yoo, Eunseob Choi, Kyeonghun Kim, Youngung Han, and Teams/Alumni.
- Confirm no broken local asset or profile URLs, JSON validity, and clean `git diff --check`.
- Configure repository-local Git identity as `khkim1729 <khkim1729@gmail.com>`, commit implementation, and push `main` to the existing origin without embedding the supplied token in any remote URL or file.

## Non-goals

- Do not modify the Google Sheet itself.
- Do not redesign the whole IMSI website or replace its static-site structure.
- Do not claim unverified KBS segment URLs or additional patent metadata.
- Do not change unrelated profiles or publication filtering behavior.
