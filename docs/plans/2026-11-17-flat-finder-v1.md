# Flat Finder v1 Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Every residential society in Gurgaon on a cinematic night map, filterable by anyone's criteria, with Divy's verified research as the example.

**Architecture:** Python pipeline (crawl, parse, merge) writes static files into `web/public/data/`. A Vite + MapLibre static site reads them and filters in the browser. Hosted on Cloudflare Pages from GitHub `kairothq/flat-finder`.

**Tech Stack:** Python 3.9 stdlib + pytest (pipeline), Vite, maplibre-gl 5.6.0, vitest (web).

**Spec:** `../../docs/superpowers/specs/2026-11-16-flat-finder-design.md` (in the parent folder), plus the approved spike `real-map-night.html`.

## Global Constraints

- Never estimate a data number. Unknown stays `null` and shows as "unknown". Generated building shapes are visual only and flagged `shape: "generated"`.
- Every data number keeps `source` (URL, plus page when from a document).
- Crawl politely: 1 request/second, cached to `pipeline/cache/` (gitignored), resumable.
- No brochure or floor-plan images are redistributed, only links.
- Style: the Night drone spike (graphite, `#ffd9a0` accent, Inter, glass panels).
- No em dashes in UI copy.

## Review Focus

1. A society with no coordinates: excluded from the map, counted in a "not located" number, never placed at 0,0.
2. A room-size filter on societies with no room data: shown as "not checked yet", never as pass or fail.
3. Duplicate projects (phases listed separately, e.g. "Heritage One" twice): merged by name + distance < 400 m.
4. Non-flat projects (plots, commercial, villas only): kept but tagged by type and filterable out, flats shown by default.
5. Phone width under 500 px: filters in a bottom sheet, no globe intro, map stays usable.

---

### Task 1: Magicbricks crawl + parse

**Files:** `pipeline/mb_crawl.py`, `pipeline/mb_parse.py`, `pipeline/tests/test_mb_parse.py`

**Interfaces:** Produces `pipeline/out/mb_projects.json`: list of `{mb_id, name, developer, locality, pincode, lat, lng, status, possession, rera_id, units, towers, acres, price_min, price_max, prop_types, amenities[str], brochure_url, url}`.

- [ ] Test `parse_list_page(html) -> list[dict]` on a saved list page: returns 20 cards with `psmName`, `pdpUrl`; `parse_total(html) == 2708`.
- [ ] Test `parse_project_page(html) -> dict` on a saved project page: lat 28.41698, lng 76.90962, `rera_id` starts with "GGM/607", amenities include "Outdoor Tennis Courts".
- [ ] Implement both from `window.SERVER_PRELOADED_STATE_` JSON (`projectDetailData.prjMobileBean.infoBean.psmLatitude/psmLongitude`, `amenitiesList[].amenityName`, `detailBean.reraId`).
- [ ] `mb_crawl.py list` fetches 136 list pages, `mb_crawl.py projects` fetches every project page, both cached and resumable.
- [ ] Commit.

### Task 2: OSM extract

**Files:** `pipeline/osm_fetch.py`, `pipeline/tests/test_osm.py`

**Interfaces:** Produces `pipeline/out/osm_buildings.geojson` (`{osm_id, h}` per building, `h` from height or levels × 3.2 or null) and `pipeline/out/osm_areas.geojson` (named residential polygons).

- [ ] Test `ring_from_relation(element)` joins outer members into closed rings.
- [ ] Fetch with mirror fallback (overpass-api.de, maps.mail.ru); bbox 28.33,76.88,28.55,77.16.
- [ ] Commit.

### Task 3: Merge into city file + shapes

**Files:** `pipeline/build_city.py`, `pipeline/shapes.py`, `pipeline/verified.py`, `pipeline/tests/test_build.py`

**Interfaces:** Consumes Task 1 and 2 outputs and the research in `~/Divys Workspace/3. Resouces/Flat hunting`. Produces `web/public/data/gurgaon.json` (schema in spec: societies, unit_types, amenities, events) and `web/public/data/gurgaon-buildings.geojson` (`{sid, h, shape: "osm"|"generated"}`).

- [ ] Test `match_area(project, areas)`: Heritage One project point matches OSM area "Heritage One".
- [ ] Test `dedupe(projects)`: two "Heritage One" entries 150 m apart become one.
- [ ] Test `generate_towers(polygon_or_point, towers, seed) -> list[Polygon]`: count == towers (default 4 when unknown), all inside polygon, deterministic for a seed.
- [ ] Test `load_verified()`: Pioneer Araya gets a unit type with bedroom `11.58 x 16.0`, confidence "primary", source page 12; Heritage One 3 BHK has `rooms_complete` false unless all bedrooms are known.
- [ ] Events: one per verified finding (`findings.md` lines plus workbook sources).
- [ ] Commit.

### Task 4: Web app

**Files:** `web/index.html`, `web/src/main.js`, `web/src/map.js`, `web/src/filters.js`, `web/src/ui.js`, `web/src/feed.js`, `web/src/style.css`, `web/src/filters.test.js`

**Interfaces:** Consumes the Task 3 files. `filters.js` exports `matchSociety(society, criteria) -> "match"|"likely"|"unknown"|"no"`, with criteria `{bhk[], minBedroom:{a,b}|null, sqftMin, sqftMax, amenities[], priceMax, status[], types[]}`.

- [ ] Tests: a bedroom 11'7"×16'0" passes min 11'3"×12'3"; 10'0"×14'0" fails (orientation-free on both sides); no room data gives "unknown"; `rooms_complete` false gives "likely".
- [ ] Map: spike look; buildings coloured by match state; click a society opens its card and plays its events in the research log; "Divy's search" preset; Replay intro; Tour button flies through matches.
- [ ] Phone layout under 700 px: bottom sheet and list, no globe intro.
- [ ] `npm run build` passes; screenshot check at 1600×900 and 390×844.
- [ ] Commit.

### Task 5: Ship

- [ ] Create `kairothq/flat-finder` (public), push, deploy to Cloudflare Pages (`wrangler pages deploy web/dist`). Confirm with Divy before pushing and deploying.
- [ ] README: what it is, data sources, how to add a city.

Skill and CLI follow in plan v2, once v1 data and site are live.
