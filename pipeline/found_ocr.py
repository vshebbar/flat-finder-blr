"""OCR floor plans that were found on other sites (data/verified/<city>-found-plans.json).

usage: uv run --with pyobjc-framework-Vision --with pyobjc-framework-Quartz python found_ocr.py gurgaon
       -> data/verified/<city>-found.json

Images go through the floor plan reader (complete when the bedroom count matches the BHK);
PDFs go through the brochure reader (never complete: a page can hold two unit plans).
"""
import hashlib
import json
import pathlib
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

import brochure_ocr
import plan_ocr

ROOT = pathlib.Path(__file__).parent
CACHE = ROOT / "cache" / "found"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def read_one(job):
    sid, plan = job
    url, kind = plan["url"], plan.get("kind") or ("pdf" if url.lower().split("?")[0].endswith(".pdf") else "image")
    if kind == "pdf":
        _, r = brochure_ocr.read_brochure((sid, url))
        return sid, {"url": url, "kind": "pdf", "found_on": plan.get("found_on"), "status": r["status"], "pages": r.get("pages", [])}
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".img")
    if not f.exists():
        subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "60", "-o", str(f), url], capture_output=True)
    if not f.exists() or f.stat().st_size < 2000:
        return sid, {"url": url, "kind": "image", "status": "download failed"}
    try:
        from ocr import ocr
        beds = plan_ocr.bedrooms_from_boxes(ocr(f))
    except Exception as e:
        return sid, {"url": url, "kind": "image", "status": "ocr error", "error": str(e)[:120]}
    bhk = plan.get("bhk")
    complete = bool(beds) and bhk is not None and len(beds) == bhk
    return sid, {"url": url, "kind": "image", "found_on": plan.get("found_on"), "bhk": bhk, "bedrooms": beds,
                 "status": "read" if complete else ("partial" if beds else "no sizes found")}


def main(city="gurgaon"):
    src = ROOT.parent / "data" / "verified" / f"{city}-found-plans.json"
    if not src.exists():
        print("nothing found yet")
        return
    found = json.loads(src.read_text())["societies"]
    # dcjain.com prints sizes including the walls, which overstates rooms: leave it out
    jobs = [(sid, p) for sid, v in found.items() for p in v.get("plans", []) if "dcjain" not in (p["url"] + (p.get("found_on") or "")).lower()]
    out = {}
    with ProcessPoolExecutor(max_workers=4) as ex:
        for sid, r in ex.map(read_one, jobs):
            out.setdefault(sid, []).append(r)
    (ROOT.parent / "data" / "verified" / f"{city}-found.json").write_text(json.dumps({"societies": out}, indent=0))
    from collections import Counter
    print(Counter(r["status"] for v in out.values() for r in v))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "gurgaon")
