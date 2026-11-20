"""Read bedroom sizes from builder brochure PDFs: render each page, OCR it locally, pair sizes with room labels.

usage: uv run --with pyobjc-framework-Vision --with pyobjc-framework-Quartz python brochure_ocr.py gurgaon
       -> data/verified/<city>-brochures.json

A page counts as a unit plan when it has bedroom labels with sizes. Its BHK comes from text printed on the
page ("3 BHK", "4 BED ROOM"); when the number of bedrooms found equals it, the reading is complete.
PDFs and page images are deleted after reading; only the readings are kept.
"""
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from concurrent.futures import ProcessPoolExecutor

import plan_ocr

ROOT = pathlib.Path(__file__).parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
MAX_PAGES, MAX_MB, DPI, SCAN_DPI, MAX_PLAN_PAGES = 40, 80, 220, 60, 10
PLAN_PAGE = re.compile(r"BHK|B\.H\.K|BED|UNIT|FLOOR\s*PLAN|TYPE|SQ\.?\s*FT|SQFT|SUPER|CARPET|LIVING|KITCHEN|TOILET|DINING|BALCONY", re.I)
BHK_TEXT = re.compile(r"\b([1-6])\s*(?:\+\s*\d\s*)?(?:BHK|B\.H\.K|BED\s*-?\s*ROOMS?|BR\b)", re.I)


def page_bhk(boxes):
    found = [int(m.group(1)) for t, *_ in boxes for m in BHK_TEXT.finditer(plan_ocr.clean(t))]
    return max(set(found), key=found.count) if found else None


def read_brochure(job):
    sid, url = job
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="ff-broch-"))
    try:
        pdf = tmp / "b.pdf"
        # curl uses the macOS trust store (HRERA's certificate chain fails in Python's own store)
        r = subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "180", "--max-filesize", str(int(MAX_MB * 1e6)), "-o", str(pdf), url], capture_output=True)
        if r.returncode == 63:
            return sid, {"url": url, "status": "too large"}
        if r.returncode != 0 or not pdf.exists():
            return sid, {"url": url, "status": "error", "error": f"download failed ({r.returncode})"}
        if pdf.read_bytes()[:4] != b"%PDF":
            return sid, {"url": url, "status": "not a pdf"}
        from ocr import ocr
        # pass 1: a quick low-resolution look at every page, to find the ones that look like unit plans
        subprocess.run(["pdftoppm", "-r", str(SCAN_DPI), "-l", str(MAX_PAGES), "-png", str(pdf), str(tmp / "s")], capture_output=True, timeout=600)
        scored = []
        for png in sorted(tmp.glob("s-*.png")):
            words = " ".join(t for t, *_ in ocr(png))
            hits = len(PLAN_PAGE.findall(words))
            if hits >= 3 and re.search(r"BED|BHK|B\.H\.K", words, re.I):
                scored.append((hits, int(png.stem.split("-")[-1])))
            png.unlink()
        candidates = sorted(n for _, n in sorted(scored, reverse=True)[:MAX_PLAN_PAGES])
        # pass 2: only those pages at full resolution, read in tiles
        pages = []
        for n in candidates:
            subprocess.run(["pdftoppm", "-r", str(DPI), "-f", str(n), "-l", str(n), "-png", str(pdf), str(tmp / "p")], capture_output=True, timeout=300)
            for png in tmp.glob("p-*.png"):
                boxes = ocr(png)
                beds = plan_ocr.bedrooms_from_boxes(boxes)
                if beds:
                    pages.append({"page": n, "bhk": page_bhk(boxes), "bedrooms": beds})
                png.unlink()
        return sid, {"url": url, "status": "read" if pages else "no unit plans found", "pages": pages}
    except Exception as e:
        return sid, {"url": url, "status": "error", "error": str(e)[:160]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(city="gurgaon"):
    data = json.loads((ROOT.parent / "web" / "public" / "data" / f"{city}.json").read_text())
    out_file = ROOT.parent / "data" / "verified" / f"{city}-brochures.json"
    done = json.loads(out_file.read_text())["brochures"] if out_file.exists() else {}
    def has_rooms(s):
        return any(u.get("bedrooms") or u.get("ai") for u in s["unit_types"])
    pool = [s for s in data["societies"] if s["kind"] in ("apartment", "builder floor")
            and (s.get("brochure_url") or "").lower().endswith(".pdf") and s["id"] not in done]
    pool = [s for s in pool if not has_rooms(s)] if "--all" not in sys.argv else pool
    pool.sort(key=lambda s: (has_rooms(s), -((s.get("sale_count") or 0) + (s.get("rent_count") or 0))))  # unread societies first
    jobs = [(s["id"], s["brochure_url"]) for s in pool]
    print("brochures to read", len(jobs), flush=True)
    with ProcessPoolExecutor(max_workers=6) as ex:
        for i, (sid, r) in enumerate(ex.map(read_brochure, jobs), 1):
            done[sid] = r
            if i % 20 == 0 or i == len(jobs):
                print(f"{i}/{len(jobs)}", flush=True)
                out_file.write_text(json.dumps({"engine": "pdftoppm + macOS Vision OCR", "brochures": done}, indent=0))
    from collections import Counter
    print(Counter(r["status"] for r in done.values()))
    print("unit pages", sum(len(r.get("pages", [])) for r in done.values()))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "gurgaon")
