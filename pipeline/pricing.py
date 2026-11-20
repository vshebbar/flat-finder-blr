"""Buy and rent prices per society and BHK, from live listings, plus labelled estimates where listings are missing.

Estimates (never shown as listing data):
  - rent from sale price, or sale from rent, using the rental yield (annual rent / price) measured on
    societies that have both, taken from the same locality when it has enough pairs, else the city per BHK;
  - when a society has neither, sale = unit size x the project's price per sq ft, then rent via yield.

Flags: listing medians that look like typos (far from the same BHK in the same locality, an impossible rent to
price ratio, or a wild price per sq ft) stay in the data and are shown, but carry a reason in p["flags"] and are
not used for matching, sorting or estimates.
"""
import math
import statistics
from collections import defaultdict

MIN_LOCALITY_PAIRS = 4
FAR = 8          # a median this many times above or below the typical value is flagged (4x still hit real luxury and affordable homes)
MIN_PEERS = 5    # societies needed to say what is typical


def stats(values):
    v = sorted(x for x in values if x)
    if not v:
        return None
    return {"median": round(statistics.median(v)), "min": round(v[0]), "max": round(v[-1]), "n": len(v)}


def listing_stats(project):
    """{bhk: {"buy": stats, "rent": stats, "psf": median price per sq ft}} from the sample listings."""
    out = defaultdict(dict)
    for kind, key in (("buy", "sale_listings"), ("rent", "rent_listings")):
        by = defaultdict(list)
        for l in project.get(key) or []:
            if l.get("bhk") and l.get("price"):
                by[l["bhk"]].append(l)
        for bhk, ls in by.items():
            out[bhk][kind] = stats(l["price"] for l in ls)
            if kind == "buy":
                psf = [l["psf"] for l in ls if l.get("psf")]
                if psf:
                    out[bhk]["psf"] = round(statistics.median(psf))
    return dict(out)


def fit_yields(societies):
    """Rental yields from societies with both buy and rent medians for the same BHK."""
    pairs = []
    for s in societies:
        for bhk, p in s["prices"].items():
            if p.get("buy") and p.get("rent"):
                y = p["rent"]["median"] * 12 / p["buy"]["median"]
                if 0.005 < y < 0.12:  # drop obvious listing mistakes (e.g. rent typed as yearly)
                    pairs.append((s.get("locality"), bhk, y, p["buy"]["median"], p["rent"]["median"]))
    by_loc, by_bhk = defaultdict(list), defaultdict(list)
    for loc, bhk, y, _, _ in pairs:
        by_loc[loc].append(y)
        by_bhk[bhk].append(y)
    city = statistics.median([p[2] for p in pairs]) if pairs else 0.03
    corr = None
    if len(pairs) > 3:
        xs, ys = [math.log(p[3]) for p in pairs], [math.log(p[4]) for p in pairs]
        mx, my = statistics.mean(xs), statistics.mean(ys)
        cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
        den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
        corr = cov / den if den else None
    model = {
        "pairs": len(pairs),
        "city_yield": round(city, 4),
        "bhk_yield": {b: round(statistics.median(v), 4) for b, v in by_bhk.items() if len(v) >= 3},
        "locality_yield": {l: round(statistics.median(v), 4) for l, v in by_loc.items() if len(v) >= MIN_LOCALITY_PAIRS and l},
        "log_price_rent_correlation": round(corr, 3) if corr is not None else None,
    }
    return model


def yield_for(model, locality, bhk):
    if locality in model["locality_yield"]:
        return model["locality_yield"][locality], f"rental yield in {locality}"
    if bhk in model["bhk_yield"]:
        return model["bhk_yield"][bhk], f"city rental yield for {bhk} BHK"
    return model["city_yield"], "city rental yield"


def inr(v):
    return f"₹{v / 1e7:.2f} Cr" if v >= 1e7 else f"₹{v / 1e5:.1f} L" if v >= 1e5 else f"₹{v / 1e3:.0f}k"


def flag_outliers(societies):
    """Add p["flags"] = {"buy"|"rent"|"buy_range"|"rent_range": reason} to price cells that look wrong."""
    peers, psf = defaultdict(list), defaultdict(list)
    for s in societies:
        for bhk, p in s["prices"].items():
            for kind in ("buy", "rent"):
                if p.get(kind):
                    peers[(s.get("locality"), bhk, kind)].append(p[kind]["median"])
                    peers[(None, bhk, kind)].append(p[kind]["median"])
            if p.get("psf"):
                psf[(s.get("locality"),)].append(p["psf"])
                psf[(None,)].append(p["psf"])

    def typical(table, loc, *key):
        for where, k in ((loc, (loc, *key)), ("the city", (None, *key))):
            if len(table[k]) >= MIN_PEERS:
                return statistics.median(table[k]), where
        return None, None

    def backed(s, p, kind, value):
        """The society's own data agrees with this value: its builder price range, or a sane rent to price ratio."""
        other = p.get("rent" if kind == "buy" else "buy")
        if other:
            y = (value if kind == "rent" else other["median"]) * 12 / (other["median"] if kind == "rent" else value)
            if 0.012 <= y <= 0.06:
                return True
        lo, hi = s.get("price_min"), s.get("price_max")
        return kind == "buy" and bool(lo and hi) and lo * 0.6 <= value <= hi * 1.6

    n = 0
    for s in societies:
        loc = s.get("locality")
        for bhk, p in s["prices"].items():
            flags = {}
            for kind, word in (("buy", "price"), ("rent", "rent")):
                st = p.get(kind)
                if not st:
                    continue
                ref, where = typical(peers, loc, bhk, kind)
                if ref and not (ref / FAR <= st["median"] <= ref * FAR) and not backed(s, p, kind, st["median"]):
                    flags[kind] = (f"{inr(st['median'])} is {st['median'] / ref:.1f}x the typical {bhk} BHK {word} in {where} "
                                   f"({inr(ref)}); may be a listing typo, check the listing")
                if st["n"] >= 2 and (st["max"] > st["median"] * FAR or st["min"] < st["median"] / FAR):
                    flags[f"{kind}_range"] = "some listings are far from the others (probably typos); the median is still usable"
            if p.get("buy") and p.get("rent") and "buy" not in flags and "rent" not in flags:
                y = p["rent"]["median"] * 12 / p["buy"]["median"]
                if y > 0.10:
                    flags["rent"] = f"rent would be {y:.0%} of the price a year (usually 2 to 4%); the rent or price may be wrong"
                elif y < 0.006:
                    flags["rent"] = f"rent would be only {y:.1%} of the price a year (usually 2 to 4%); the rent or price may be wrong"
            if p.get("psf") and "buy" not in flags:
                ref, where = typical(psf, loc)
                if ref and not (ref / FAR <= p["psf"] <= ref * FAR):
                    flags["buy"] = (f"₹{p['psf']:,}/sq ft is {p['psf'] / ref:.1f}x the typical in {where} (₹{ref:,.0f}); "
                                    "the price or the size may be mistyped")
            if flags:
                p["flags"] = flags
                n += 1
    return n


def usable(p, kind):
    """A listing median that is present and not flagged."""
    return p.get(kind) and kind not in p.get("flags", {}) and p[kind]["median"]


def add_estimates(s, model, sizes_by_bhk, psf_fallback):
    """Fill buy_est / rent_est for each BHK of a society that lacks listings."""
    bhks = set(s["prices"]) | set(sizes_by_bhk)
    for bhk in bhks:
        p = s["prices"].setdefault(bhk, {})
        y, why = yield_for(model, s.get("locality"), bhk)
        buy = usable(p, "buy")
        rent = usable(p, "rent")
        if not buy and rent:
            p["buy_est"] = {"value": round(rent * 12 / y, -4), "basis": f"rent ÷ {why} ({y:.1%})"}
            buy = p["buy_est"]["value"]
        if not buy and sizes_by_bhk.get(bhk) and psf_fallback:
            p["buy_est"] = {"value": round(sizes_by_bhk[bhk] * psf_fallback, -4),
                            "basis": f"{int(sizes_by_bhk[bhk]):,} sq ft × ₹{int(psf_fallback):,}/sq ft"}
            buy = p["buy_est"]["value"]
        if not rent and buy:
            p["rent_est"] = {"value": round(buy * y / 12, -2), "basis": f"price × {why} ({y:.1%})"}
        if not p:
            del s["prices"][bhk]
