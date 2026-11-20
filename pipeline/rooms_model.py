"""Cautious estimate of the smallest bedroom from unit size, for units whose plans have not been read.

Fitted on verified unit types: smallest bedroom short side and area against ln(sq ft per bedroom).
We publish only a LOWER BOUND (prediction minus the worst shortfall seen in the verified data), so an
estimate can say "probably at least this big" and never overstates a room.
"""
import math


def _fit(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    return my - b * mx, b


def fit(verified_societies):
    pts = []
    for s in verified_societies:
        for u in s["unit_types"]:
            size = u.get("super_sqft") or (u.get("carpet_sqft") and u["carpet_sqft"] * 1.35)  # carpet -> super, typical loading
            if not (u["bedrooms"] and size and u.get("bhk") and u["rooms_complete"]):
                continue
            x = math.log(size / u["bhk"])
            pts.append((x, min(r[0] for r in u["bedrooms"]), min(r[0] * r[1] for r in u["bedrooms"])))
    if len(pts) < 8:
        return None
    xs = [p[0] for p in pts]
    a1, b1 = _fit(xs, [p[1] for p in pts])
    a2, b2 = _fit(xs, [p[2] for p in pts])
    short_gap = max(0.0, max((a1 + b1 * x) - y for x, y, _ in pts))
    area_gap = max(0.0, max((a2 + b2 * x) - z for x, _, z in pts))
    return {"n": len(pts), "short": [round(a1, 4), round(b1, 4), round(short_gap, 3)], "area": [round(a2, 3), round(b2, 3), round(area_gap, 2)]}


def lower_bounds(model, size_sqft, bhk):
    """(short side ft, area sq ft) the smallest bedroom is probably at least, or None."""
    if not model or not size_sqft or not bhk:
        return None
    x = math.log(size_sqft / bhk)
    a1, b1, g1 = model["short"]
    a2, b2, g2 = model["area"]
    # never extrapolate beyond the largest verified homes: cap the gain at the top of the fitted range
    return round(a1 + b1 * min(x, math.log(1600)) - g1, 2), round(a2 + b2 * min(x, math.log(1600)) - g2)
