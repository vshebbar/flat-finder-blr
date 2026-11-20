"""Find each society's HRERA Gurugram filing and OCR its brochure / apartment plan documents.

usage: uv run --with pyobjc-framework-Vision --with pyobjc-framework-Quartz python hrera.py gurgaon [limit]
       -> data/verified/<city>-hrera.json

HRERA pages are public and load without login. Pages are fetched one per second; documents are read
with the brochure pipeline (render, OCR, pair sizes with room labels) and deleted afterwards.
"""
import json
import pathlib
import re
import sys
import time
import urllib.request
from concurrent.futures import ProcessPoolExecutor

import brochure_ocr
from build_city import tokens

ROOT = pathlib.Path(__file__).parent
CACHE = ROOT / "cache" / "hrera"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
LIST_URL = "https://haryanarera.gov.in/admincontrol/registered_projects/2"  # Gurugram authority
WANT = re.compile(r"BROCHURE|APARTMENT\s*PLAN|UNIT\s*PLAN|FLOOR\s*PLAN|TYPICAL\s*FLOOR|DWELLING\s*UNIT|AREA\s*DIAGRAM|APPROVED\s*BUILDING\s*PLAN|BUILDING\s*PLAN(?!.*(LETTER|APPROVAL))", re.I)
SKIP = re.compile(r"LAYOUT|SITE\s*PLAN|ZONING|DEMARCATION|SERVICE|LICEN|CASH|AFFIDAVIT|BANK|CERTIFICATE|PAYMENT|AGREEMENT", re.I)


def get(url, cache_name=None):
    if cache_name:
        f = CACHE / cache_name
        if f.exists():
            return f.read_text(errors="ignore")
    import subprocess
    r = subprocess.run(["curl", "-sL", "-A", UA, "--max-time", "120", url], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"curl failed ({r.returncode})")
    html = r.stdout.decode("utf-8", "ignore")
    time.sleep(1)
    if cache_name:
        CACHE.mkdir(parents=True, exist_ok=True)
        (CACHE / cache_name).write_text(html)
    return html


def cells_of(row):
    return [re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]


def registered_projects():
    html = get(LIST_URL, "registered_2.html")
    out = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        c = cells_of(row)
        link = [l for l in re.findall(r'href="([^"]+)"', row) if "project_preview" in l]
        if len(c) >= 6 and link:
            out.append({"reg": c[1], "rera": c[2], "name": c[3], "promoter": c[4], "address": c[5], "url": link[0]})
    return out


def norm_reg(t):
    return re.sub(r"[^0-9A-Z/]", "", (t or "").upper().split("DATED")[0])


def sector_of(t):
    m = re.search(r"SECTOR[\s-]*(\d+[A-Z]?)", (t or "").upper())
    return m.group(1) if m else None


def match(society, projects):
    rid = norm_reg(society.get("rera_id"))
    if rid and len(rid) >= 6:
        for p in projects:
            for r in re.split(r"/(?=[A-Z])|,|AND", society["rera_id"].upper()):
                r = norm_reg(r)
                if len(r) >= 6 and (r in norm_reg(p["reg"]) or r == norm_reg(p["rera"])):
                    return p
    want, sec = tokens(society["name"]), sector_of(society.get("locality"))
    if not want:
        return None
    best = None
    for p in projects:
        have = tokens(p["name"])
        if want <= have and (not sec or sec == sector_of(p["address"])):
            if best is None or len(have) < len(tokens(best["name"])):
                best = p
    return best


def documents(project_url):
    html = get(project_url)
    docs = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        if "view_uploaded_Document_open" not in row:
            continue
        c = cells_of(row)
        name = c[1] if len(c) > 1 else ""
        link = re.search(r'href="([^"]+view_uploaded_Document_open[^"]+)"', row).group(1)
        if WANT.search(name) and not SKIP.search(name):
            docs.append({"name": name, "url": link})
    return docs


def run(job):
    sid, d = job
    _, r = brochure_ocr.read_brochure((sid, d["url"]))
    return sid, d["name"], r


def main(city="gurgaon", limit=None):
    data = json.loads((ROOT.parent / "web" / "public" / "data" / f"{city}.json").read_text())
    out_file = ROOT.parent / "data" / "verified" / f"{city}-hrera.json"
    done = json.loads(out_file.read_text())["societies"] if out_file.exists() else {}
    projects = registered_projects()
    print("HRERA Gurugram projects", len(projects), flush=True)

    def has_rooms(s):
        return any(u.get("bedrooms") or u.get("ai") for u in s["unit_types"])
    pool = [s for s in data["societies"] if s["kind"] in ("apartment", "builder floor") and not s["verified"] and not has_rooms(s) and s["id"] not in done]
    pool.sort(key=lambda s: -((s.get("sale_count") or 0) + (s.get("rent_count") or 0)))
    if limit:
        pool = pool[:limit]
    jobs = []
    for s in pool:
        p = match(s, projects)
        if not p:
            done[s["id"]] = {"status": "no HRERA match"}
            continue
        try:
            docs = documents(p["url"])
        except Exception as e:
            done[s["id"]] = {"status": "page error", "project": p["url"], "error": str(e)[:120]}
            continue
        done[s["id"]] = {"status": "matched", "project": p["url"], "hrera_name": p["name"], "docs": [d["name"] for d in docs]}
        jobs += [(s["id"], d) for d in docs[:4]]
    print("matched", sum(1 for v in done.values() if v.get("project")), "documents to read", len(jobs), flush=True)

    with ProcessPoolExecutor(max_workers=4) as ex:
        for i, (sid, name, r) in enumerate(ex.map(run, jobs), 1):
            done[sid].setdefault("read", []).append({"doc": name, "status": r["status"], "pages": r.get("pages", [])})
            if i % 10 == 0 or i == len(jobs):
                print(f"{i}/{len(jobs)} documents", flush=True)
                out_file.write_text(json.dumps({"societies": done}, indent=0))
    out_file.write_text(json.dumps({"societies": done}, indent=0))
    from collections import Counter
    print(Counter(v["status"] for v in done.values()))
    print("societies with rooms read from HRERA", sum(1 for v in done.values() if any(x.get("pages") for x in v.get("read", []))))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "gurgaon", int(sys.argv[2]) if len(sys.argv) > 2 else None)
