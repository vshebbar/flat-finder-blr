"""Load hand-verified research and convert printed room sizes to feet."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent.parent
FILE = ROOT / "data" / "verified" / "bangalore.json"


def side_to_ft(s):
    """12'10\" -> 12.833; 3350 (mm) -> 10.991; 16' -> 16.0."""
    s = s.strip().replace("’", "'").replace("”", '"')
    m = re.fullmatch(r"(\d+)'(?:\s*(\d+(?:\.\d+)?)\")?", s)
    if m:
        return round(int(m.group(1)) + float(m.group(2) or 0) / 12, 3)
    m = re.fullmatch(r"\d+(?:\.\d+)?", s)
    if m:
        v = float(s)
        return round(v / 304.8, 3) if v > 100 else v
    raise ValueError(f"cannot read side {s!r}")


def room_to_ft(r):
    a, b = re.split(r"\s*[x×]\s*", r.strip())
    a, b = side_to_ft(a), side_to_ft(b)
    return [min(a, b), max(a, b)]


def unit_from_verified(u):
    rooms = [room_to_ft(r) for r in u.get("bedrooms", [])]
    complete = bool(rooms) and not u.get("smallest_only") and (
        u.get("others_larger") or len(rooms) >= (u.get("bhk") or 0))
    return {
        "label": u["label"],
        "bhk": u.get("bhk"),
        "super_sqft": u.get("super_sqft"),
        "carpet_sqft": u.get("carpet_sqft"),
        "bedrooms": rooms,
        "bedrooms_printed": u.get("bedrooms", []),
        "rooms_complete": complete,
        "confidence": u.get("confidence"),
        "source": u.get("source"),
        "page": u.get("page"),
    }


def load_verified(path=FILE):
    data = json.loads(pathlib.Path(path).read_text())
    out = []
    for s in data["societies"]:
        out.append({
            "name": s["name"],
            "match": s.get("match", [s["name"]]),
            "sector": s.get("sector"),
            "note": s.get("note"),
            "amen_facts": s.get("amenities", {}),
            "unit_types": [unit_from_verified(u) for u in s.get("unit_types", [])],
        })
    return out
