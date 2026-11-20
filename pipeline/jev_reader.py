"""Read bedroom sizes off floor plan images with Jev (TypeSafe), keeping only confident answers.

usage: python jev_reader.py gurgaon [limit]   -> data/verified/<city>-ai.json (cache in cache/plans/)

Jev answers typed questions, so sizes are asked as multiple choice in 3-inch steps:
  min_short  the smallest shorter side among all bedrooms
  min_long   the smallest longer side among all bedrooms
  a_short / a_long  the sides of the smallest bedroom by area
Together these decide any "every bedroom at least A x B" or "at least N sq ft" filter.
A plan counts only if Jev is sure it is a floor plan with printed sizes and of its BHK;
each size counts only above MIN_CONF. Everything else stays unread rather than guessed.
"""
import base64
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).parent
CACHE = ROOT / "cache" / "plans"
URL = "https://api.typesafe.ai/v1/systemone"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
MIN_CONF = 0.75
BEDROOMS = "every bedroom (BEDROOM, BED ROOM, M. BEDROOM, MASTER, KIDS, GUEST; not servant, study or utility rooms)"


def options(lo, hi):
    out, x = {}, lo
    while x <= hi + 1e-6:
        f, i = int(x), round((x - int(x)) * 12)
        out[f"f{f}i{i}"] = f"{f}'{i}\""
        x += 0.25
    return out


def option_ft(key):
    f, i = key[1:].split("i")
    return int(f) + int(i) / 12


QUESTIONS = {
    "is_plan": {"type": "noul", "instructions": "`floor_plan` is a 2D apartment floor plan with each room's size printed in feet or millimetres"},
    "bhk": {"type": "choice", "instructions": "Number of bedrooms in `floor_plan`", "criteria": {"b1": "1", "b2": "2", "b3": "3", "b4": "4", "b5": "5 or more"}},
    "min_short": {"type": "choice", "instructions": f"In `floor_plan`, read the printed size of {BEDROOMS}. The smallest SHORTER side among them", "criteria": options(8, 14)},
}
LONG_STEPS = [10.5, 11, 11.25, 11.5, 12, 12.25, 12.5, 13, 13.5, 14, 15]
AREA_STEPS = [100, 110, 120, 130, 140, 150, 160, 180, 200]


def feet(x):
    return f"{int(x)}'{int(round((x - int(x)) * 12))}\""


LADDER = {f"long_{x}": {"type": "noul", "instructions": f"In `floor_plan`, the LONGER printed side of {BEDROOMS} is at least {feet(x)}"} for x in LONG_STEPS}
LADDER.update({f"area_{a}": {"type": "noul", "instructions": f"In `floor_plan`, {BEDROOMS} has a printed size whose length times width is at least {a} square feet"} for a in AREA_STEPS})
YES, NO = 0.75, 0.3


def bounds(ans, prefix, steps):
    """Lower bound = highest step confirmed with every step below it also confirmed; upper = lowest step confidently denied."""
    lb = ub = None
    for x in steps:
        if ans[f"{prefix}_{x}"]["noul"] >= YES and lb is not None or ans[f"{prefix}_{x}"]["noul"] >= YES and x == steps[0]:
            lb = x
        else:
            break
    for x in steps:
        if ans[f"{prefix}_{x}"]["noul"] <= NO:
            ub = x
            break
    if lb is not None and ub is not None and ub <= lb:  # contradictory ladder: trust neither
        return None, None
    return lb, ub


def key():
    for line in (pathlib.Path.home() / ".claude" / ".env").read_text().splitlines():
        if line.startswith("JEV_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("JEV_KEY not found in ~/.claude/.env")


def fetch_image(url):
    """Download once; keep a copy no larger than 1400 px on its long side (Jev rejects big images)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".jpg")
    small = f.with_suffix(".small.jpg")
    if not f.exists():
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        f.write_bytes(urllib.request.urlopen(req, timeout=40).read())
    if not small.exists():
        import subprocess
        subprocess.run(["sips", "-s", "format", "jpeg", "-Z", "1400", str(f), "--out", str(small)], capture_output=True)
        if not small.exists():
            small.write_bytes(f.read_bytes())
    return small.read_bytes()


def ask(img, questions, api_key):
    fmt = "png" if img[:4] == b"\x89PNG" else "jpg"
    body = {"model": "jev-latest", "state": {"floor_plan": "plan-image-1"},
            "assets": {"plan-image-1": {"type": "image", "format": fmt, "data_base64": base64.b64encode(img).decode()}},
            "questions": questions}
    err = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
                "Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "TypeSafe-Danger-Zone-Images": "true"})
            return json.loads(urllib.request.urlopen(req, timeout=60).read())["answers"]
        except urllib.error.HTTPError as e:
            err = f"{e.code} {e.read()[:120]!r}"
            if e.code < 500 and e.code != 429:
                break
        except Exception as e:  # network blips
            err = str(e)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(err)


def read_plan(url, bhk_hint, api_key):
    img = fetch_image(url)
    first = ask(img, QUESTIONS, api_key)
    out = {"source": url, "bhk_listed": int(bhk_hint), "is_plan": round(first["is_plan"]["noul"], 3)}
    if first["is_plan"]["noul"] < 0.8:
        out["status"] = "not a plan with sizes"
        return out
    b, ms = first["bhk"], first["min_short"]
    out["bhk"] = int(b["choice"][1]) if (b.get("confidence") or 0) >= MIN_CONF else None
    out["min_short_conf"] = round(ms.get("confidence") or 0, 3)
    out["min_short"] = round(option_ft(ms["choice"]), 3) if out["min_short_conf"] >= MIN_CONF else None
    lad = ask(img, LADDER, api_key)
    out["long_lb"], out["long_ub"] = bounds(lad, "long", LONG_STEPS)
    out["area_lb"], out["area_ub"] = bounds(lad, "area", AREA_STEPS)
    out["ladder"] = {k: round(v["noul"], 2) for k, v in lad.items()}
    bhk_ok = out["bhk"] in (None, int(bhk_hint)) or int(bhk_hint) >= 5
    out["status"] = "read" if out["min_short"] is not None and bhk_ok else "unsure"
    return out


def main(city="gurgaon", limit=None):
    data = json.loads((ROOT.parent / "web" / "public" / "data" / f"{city}.json").read_text())
    pool = [s for s in data["societies"] if s["kind"] in ("apartment", "builder floor") and s.get("plan_links")]
    pool.sort(key=lambda s: -((s.get("sale_count") or 0) + (s.get("rent_count") or 0)))
    if limit:
        pool = pool[:limit]
    out_file = ROOT.parent / "data" / "verified" / f"{city}-ai.json"
    done = json.loads(out_file.read_text())["plans"] if out_file.exists() else {}
    api_key = key()
    jobs = [(s["id"], b, u) for s in pool for b, urls in s["plan_links"].items() for u in urls[:3] if u not in done]
    print("plans to read", len(jobs), flush=True)
    t0 = time.time()

    def one(job):
        sid, b, u = job
        try:
            r = read_plan(u, b, api_key)
        except Exception as e:
            r = {"source": u, "status": "error", "error": str(e)[:160]}
        r["sid"] = sid
        return u, r

    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, (u, r) in enumerate(ex.map(one, jobs), 1):
            done[u] = r
            if i % 100 == 0 or i == len(jobs):
                print(f"{i}/{len(jobs)} plans, {time.time() - t0:.0f}s", flush=True)
                out_file.write_text(json.dumps({"model": "jev-latest", "min_conf": MIN_CONF, "plans": done}, indent=0))
    from collections import Counter
    print(Counter(r["status"] for r in done.values()))
    print("societies with a read plan", len({r["sid"] for r in done.values() if r["status"] == "read"}))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "gurgaon", int(sys.argv[2]) if len(sys.argv) > 2 else None)
