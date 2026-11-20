# Flat Finder

Every housing society in a city on one night map. Set the smallest bedroom you can live with, size, BHK, amenities and budget, and watch the societies that fit light up. Every number links to where it came from.

Gurugram is first: about 2,700 projects from Magicbricks, building outlines from OpenStreetMap, and a set of societies verified by reading builder brochures and HRERA plans.

## What the colours mean

- **Bright**: matches your search.
- **Amber**: likely. The rooms we have read pass, but not every bedroom has been read yet.
- **Faint outline**: not checked yet. We have no room sizes for it, so it is neither a pass nor a fail.
- **Dark**: does not match.

Building shapes come from OpenStreetMap where they are mapped. Where they are not, towers are drawn from the listed tower count and say "approximate shape" on the card. Shapes are visual only; data numbers are never estimated.

## How bedroom sizes are read

Four sources, most trusted first. Each unit on a card says which one it came from.

1. **Checked by hand**: rooms read from builder brochures or HRERA plans by a person, page cited (`data/verified/<city>.json`).
2. **OCR of a floor plan image**: macOS's built-in text recognition reads every printed size on the plan; code pairs each size with its own room label and takes the smallest bedroom. Free and local (`pipeline/plan_ocr.py`). Where Jev also read the plan, the two must agree within 2 inches.
3. **OCR of brochures and HRERA filings**: the same reading on brochure pages and HRERA "approved building plans" (`pipeline/brochure_ocr.py`, `pipeline/hrera.py`). A page can hold two unit plans, so these are never "complete": a failing room still fails, passing rooms only make a society "likely".
4. **Jev (TypeSafe)**: a fast typed-decision model that answers multiple-choice and yes/no questions about the plan image (`pipeline/jev_reader.py`). Used as a cross-check and a fallback. In spot checks it overstated a room about 1 time in 10, so a Jev-only reading is never more than "likely".

Bedrooms under 8 ft wide are dropped as mis-pairings. Plans that are 3D renders without printed sizes are skipped.

## Buy or rent

Every society shows buy prices and monthly rents per BHK: medians, ranges and counts of live Magicbricks listings (22,018 homes for sale and 7,371 for rent in Gurugram). Where a society has no listings, the site shows **our estimate, marked "~"**, with the working shown:

- rent from price (or price from rent) using the rental yield measured on 960 society and BHK pairs that have both (about 2.5% of the price per year, correlation between log price and log rent 0.91), using the locality's own yield where it has at least 4 pairs;
- when there are no listings at all, unit size x the project's price per sq ft, then rent via yield.

Cards also show resident ratings by category, review snippets, the 5-year price per sq ft trend, and links to Google Maps (with Google reviews) and directions.

## Download the data

- `/data/gurgaon-societies.csv`: one row per society (location, type, listings, buy and rent medians and estimates per BHK, ratings, amenities, links).
- `/data/gurgaon-units.csv`: one row per unit type, with bedroom sizes and sources.
- "Export these results" on the site downloads whatever your filters currently match.

## Use it inside Claude (connector)

Flat Finder is an MCP server at `https://flat-finder.pages.dev/mcp`. In Claude, add a custom connector with that URL, then ask things like "3 BHK in Gurgaon under ₹80k rent, every bedroom at least 11 by 12, park within 500 m". Tools: `search_societies` (any sector, budget, size, amenity, distance; up to 200 results per call), `breakdown` (group by sector, BHK, amenity, metro distance or rent band), `list_localities`, `get_society` (with reviews and rating categories), `compare_societies`. Listing prices that look like typos are flagged with a reason and not used for filtering.

## Search from a terminal

```bash
npx github:kairothq/flat-finder --bhk 3,4 --min-bedroom "11'3x12'3" --min-sqft 1620 --amenity squash --likely
npx github:kairothq/flat-finder --bhk 3 --max-rent 80k --amenity pool
```

## Use it with Claude Code

`skills/flat-finder/SKILL.md` is a Claude Code skill. Copy it into `~/.claude/skills/flat-finder/` and ask Claude to "add Bangalore to flat finder", "verify Ireo Skyon", or "find me a 3 BHK with every bedroom at least 11 by 12 feet". It follows the same rules as this repo: primary sources first, never estimate, every number keeps its page.

## Run it

```bash
# data
cd pipeline
python3 mb_crawl.py list gurgaon && python3 mb_crawl.py projects gurgaon   # polite, cached, resumable
python3 osm_fetch.py gurgaon
python3 build_city.py gurgaon                                               # -> web/public/data/

# site
cd ../web && npm install && npm run dev
```

Tests: `cd pipeline && uv run --with pytest pytest` and `cd web && npx vitest run --root .. cli web/src`.

Cities live in `data/cities.json`. Gurugram is built; Bengaluru and Mumbai are configured and need the pipeline run (see the skill, Job 2).

Press `/` to search for a society. The Streets button switches to a street map with road and sector names.

Useful links: `?city=gurgaon`, `?map=streets` or `?map=light`, `?preset=divy` loads the example search, `?open=<society id>` opens one society, `?nointro` skips the globe fly-in.

## Add verified research

Verified rows live in `data/verified/<city>.json`. Each unit type lists its bedrooms exactly as printed (`12'10"x16'4"` or millimetres `3350x3750`) with the source URL and page. Open a pull request, or use "Research this society" on any card to request one.

## Sources

Magicbricks project pages (listing facts, live sale and rent listings, resident ratings and reviews), OpenStreetMap contributors (outlines, ODbL), Esri World Imagery (basemap), OpenFreeMap (roads and city buildings), HRERA Gurugram and builder brochures (verified rows).
