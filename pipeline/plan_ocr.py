"""Read every bedroom's printed size off floor plan images with local OCR (macOS Vision), cross-checked by Jev.

usage: uv run --with pyobjc-framework-Vision --with pyobjc-framework-Quartz python plan_ocr.py gurgaon
       -> data/verified/<city>-ocr.json

OCR returns text boxes; code pairs each bedroom label with the size printed under or beside it, so the
"smallest of all bedrooms" is arithmetic, not a model's judgement. A plan counts as read when the number
of bedrooms found equals its BHK. Where Jev also read the plan, its narrowest side must agree within 2 inches,
otherwise the plan is flagged for review rather than published.
"""
import hashlib
import json
import pathlib
import re
import sys
from concurrent.futures import ProcessPoolExecutor

ROOT = pathlib.Path(__file__).parent
CACHE = ROOT / "cache" / "plans"

BED = re.compile(r"\b(M\.?\s*|MASTER\s*|KIDS?\s*|GUEST\s*)?(BED\s*-?\s*ROOM|BEDROOM|BED\s*RM|B\.?\s*R\.?\b)|\bKIDS?\s*ROOM|\bGUEST\s*ROOM", re.I)
NOT_BED = re.compile(r"TOILET|BATH|WASH|DRESS|BALCONY|LOBBY|W\.?C\b|SERVANT|STAFF|UTILITY|STORE|STUDY", re.I)
FT_SIDE = r"(\d{1,2})\s*(?:'|-)\s*-?\s*(\d{1,2}(?:\.\d+)?)?\s*\"?"
FT_PAIR = re.compile(FT_SIDE + r"\s*X\s*" + FT_SIDE)
MM_PAIR = re.compile(r"\b(\d{4})\s*X\s*(\d{4})\b")
M_PAIR = re.compile(r"\b(\d{1,2}\.\d{2})\s*(?:M\s*)?X\s*(\d{1,2}\.\d{2})\b")


def clean(t):
    t = t.upper()
    for a, b in (("Х", "X"), ("×", "X"), ("*", '"'), ("’", "'"), ("‘", "'"), ("”", '"'), ("“", '"'), ("''", '"'), ("`", "'"), ("°", "'"), ("º", "'")):
        t = t.replace(a, b)
    return t


def parse_size(text):
    """Return (short, long) in feet from a printed size, or None. Handles 12'-9"X11'-4", 3350 X 3700 (mm), 4.72 X 4.19 (m)."""
    t = clean(text)
    m = FT_PAIR.search(t)
    if m and ("'" in t or '"' in t):
        a = int(m.group(1)) + float(m.group(2) or 0) / 12
        b = int(m.group(3)) + float(m.group(4) or 0) / 12
        if (m.group(2) and float(m.group(2)) >= 12) or (m.group(4) and float(m.group(4)) >= 12):
            return None
    else:
        m = MM_PAIR.search(t)
        if m:
            a, b = int(m.group(1)) / 304.8, int(m.group(2)) / 304.8
        else:
            m = M_PAIR.search(t)
            if not m:
                return None
            a, b = float(m.group(1)) * 3.28084, float(m.group(2)) * 3.28084
    a, b = sorted((a, b))
    if not (6 <= a <= 30 and 6 <= b <= 40):
        return None
    return round(a, 3), round(b, 3)


LABEL = re.compile(r"[A-Z]{3,}", re.I)


def bedrooms_from_boxes(boxes):
    """boxes: [(text, x, y, h, conf)]. Give every printed size to its own nearest room label (any room),
    then keep the ones whose label is a bedroom. A toilet's size can then never land on a bedroom."""
    sizes = [(i, parse_size(t), x, y) for i, (t, x, y, h, c) in enumerate(boxes)]
    labels = [(i, t, x, y) for i, (t, x, y, h, c) in enumerate(boxes) if LABEL.search(clean(t))]
    beds, owner = [], {}
    for i, t, x, y in labels:  # a label that carries its own size
        own = parse_size(t)
        if own and BED.search(t) and not NOT_BED.search(t):
            beds.append({"label": t.strip(), "ft": own})
            owner[i] = i
    for j, sz, sx, sy in sizes:
        if not sz or j in owner:
            continue
        best = None
        for i, t, x, y in labels:
            if i == j or i in owner.values():
                continue
            dx, dy = abs(sx - x), sy - y
            if dx < 0.12 and -0.01 <= dy < 0.07:          # printed under (or on) the room name
                d = dx + dy * 2
            elif abs(dy) < 0.012 and 0 < sx - x < 0.45:   # a size table: same line, to the right
                d = 0.05 + (sx - x) * 0.5
            else:
                continue
            if best is None or d < best[0]:
                best = (d, i, t)
        if best:
            owner[j] = best[1]
            if BED.search(best[2]) and not NOT_BED.search(best[2]):
                beds.append({"label": best[2].strip(), "ft": sz})
    # no real bedroom is under 8 ft wide: a narrower one is a size given to the wrong label
    return [b for b in beds if b["ft"][0] >= 8]


def read_image(args):
    url, bhk_hint = args
    f = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".jpg")
    if not f.exists():
        return url, {"status": "no image"}
    try:
        from ocr import ocr
        boxes = ocr(f)
    except Exception as e:
        return url, {"status": "ocr error", "error": str(e)[:120]}
    beds = bedrooms_from_boxes(boxes)
    return url, {"bedrooms": beds, "n_sizes": sum(1 for b in boxes if parse_size(b[0])), "bhk_listed": int(bhk_hint)}


def judge(r, jev):
    """Decide whether an OCR reading can be published."""
    beds = r.get("bedrooms") or []
    if not beds:
        r["status"] = "no sizes printed" if not r.get("n_sizes") else "bedrooms not found"
        return r
    want = (jev or {}).get("bhk") or r["bhk_listed"]
    r["min_short"] = min(b["ft"][0] for b in beds)
    if len(beds) != want and not (want >= 5 and len(beds) >= 5):
        r["status"] = f"found {len(beds)} bedrooms for {want} BHK"
        return r
    if jev and jev.get("min_short") is not None and abs(jev["min_short"] - r["min_short"]) > 2 / 12:
        r["status"] = "OCR and Jev disagree"
        r["jev_min_short"] = jev["min_short"]
        return r
    r["status"] = "read"
    r["checked_by"] = "OCR + Jev" if jev and jev.get("min_short") is not None else "OCR"
    return r


def main(city="gurgaon"):
    data = json.loads((ROOT.parent / "web" / "public" / "data" / f"{city}.json").read_text())
    jev = json.loads((ROOT.parent / "data" / "verified" / f"{city}-ai.json").read_text())["plans"]
    jobs, sid_of = [], {}
    for s in data["societies"]:
        for b, urls in (s.get("plan_links") or {}).items():
            for u in urls[:3]:
                jobs.append((u, b))
                sid_of[u] = s["id"]
    out = {}
    with ProcessPoolExecutor(max_workers=6) as ex:
        for i, (u, r) in enumerate(ex.map(read_image, jobs, chunksize=8), 1):
            r["sid"] = sid_of[u]
            out[u] = judge(r, jev.get(u)) if "bedrooms" in r else r
            if i % 200 == 0:
                print(f"{i}/{len(jobs)}", flush=True)
    (ROOT.parent / "data" / "verified" / f"{city}-ocr.json").write_text(json.dumps({"engine": "macOS Vision OCR + Jev check", "plans": out}, indent=0))
    from collections import Counter
    print(Counter(r["status"] for r in out.values()).most_common())
    print("societies with a read plan", len({r["sid"] for r in out.values() if r["status"] == "read"}))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "gurgaon")
