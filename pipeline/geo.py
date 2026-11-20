"""Small planar geometry helpers in lng/lat, using a local metre projection."""
import math
import random

M_PER_DEG_LAT = 111_320.0


def m_per_deg_lng(lat):
    return M_PER_DEG_LAT * math.cos(math.radians(lat))


def dist_m(a, b):
    """a, b: (lng, lat)."""
    dx = (a[0] - b[0]) * m_per_deg_lng((a[1] + b[1]) / 2)
    dy = (a[1] - b[1]) * M_PER_DEG_LAT
    return math.hypot(dx, dy)


def centroid(ring):
    pts = ring[:-1] if ring[0] == ring[-1] else ring
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def point_in_ring(pt, ring):
    x, y = pt
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi:
            inside = not inside
        j = i
    return inside


def bbox(ring):
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def circle(center, radius_m, n=24):
    lng, lat = center
    k = m_per_deg_lng(lat)
    ring = [(round(lng + radius_m * math.cos(2 * math.pi * i / n) / k, 6),
             round(lat + radius_m * math.sin(2 * math.pi * i / n) / M_PER_DEG_LAT, 6)) for i in range(n)]
    return ring + [ring[0]]


def rect(center, w_m, d_m, angle):
    lng, lat = center
    k = m_per_deg_lng(lat)
    c, s = math.cos(angle), math.sin(angle)
    pts = []
    for dx, dy in ((-w_m / 2, -d_m / 2), (w_m / 2, -d_m / 2), (w_m / 2, d_m / 2), (-w_m / 2, d_m / 2)):
        rx, ry = dx * c - dy * s, dx * s + dy * c
        pts.append((round(lng + rx / k, 6), round(lat + ry / M_PER_DEG_LAT, 6)))
    return pts + [pts[0]]


def generate_towers(ring, count, seed, w_m=24, d_m=18):
    """Place `count` tower footprints inside `ring`, spread out, deterministic for `seed`."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = bbox(ring)
    lat = (y0 + y1) / 2
    k = m_per_deg_lng(lat)
    step = 12.0  # metres between candidate points
    cands = []
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            if point_in_ring((x, y), ring):
                cands.append((x, y))
            x += step / k
        y += step / M_PER_DEG_LAT
    if not cands:
        cands = [centroid(ring)]
    # farthest-point sampling from a seeded start keeps towers spread out
    chosen = [rnd.choice(cands)]
    while len(chosen) < count:
        best = max(cands, key=lambda c: min(dist_m(c, q) for q in chosen))
        if min(dist_m(best, q) for q in chosen) < 10:  # site too small for more
            break
        chosen.append(best)
    angle = rnd.uniform(0, math.pi / 2)
    return [rect(c, w_m, d_m, angle) for c in chosen]


def area_m2(ring):
    lat = sum(p[1] for p in ring) / len(ring)
    k = m_per_deg_lng(lat)
    a = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        a += (x1 * k) * (y2 * M_PER_DEG_LAT) - (x2 * k) * (y1 * M_PER_DEG_LAT)
    return abs(a) / 2
