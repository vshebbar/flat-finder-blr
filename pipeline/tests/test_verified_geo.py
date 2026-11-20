import geo
import verified


def test_side_to_ft():
    assert verified.side_to_ft("12'10\"") == 12.833
    assert verified.side_to_ft("3350") == 10.991
    assert verified.side_to_ft("16'0\"") == 16.0


def test_room_sorted_short_side_first():
    assert verified.room_to_ft("15'6\"x11'0\"") == [11.0, 15.5]


def test_load_verified_araya_and_heritage():
    v = {s["name"]: s for s in verified.load_verified()}
    ar = v["Pioneer Araya"]["unit_types"][0]
    assert [11.583, 16.0] in v["Pioneer Urban Presidia"]["unit_types"][0]["bedrooms"]
    assert ar["confidence"] == "primary" and ar["page"] == "17" and ar["rooms_complete"]
    h3 = v["Conscient Heritage One"]["unit_types"][0]
    assert h3["rooms_complete"] and [11.25, 12.25] in h3["bedrooms"]
    polo = v["M3M Polo Suites"]["unit_types"][0]
    assert polo["rooms_complete"] is False  # only the smallest room is known


def test_generate_towers_inside_and_deterministic():
    ring = geo.circle((77.08, 28.40), 150)
    a = geo.generate_towers(ring, 5, seed=7)
    b = geo.generate_towers(ring, 5, seed=7)
    assert a == b and len(a) == 5
    for t in a:
        assert geo.point_in_ring(geo.centroid(t), ring)


def test_generate_towers_small_site_caps_count():
    ring = geo.circle((77.08, 28.40), 12)
    assert 1 <= len(geo.generate_towers(ring, 20, seed=1)) < 20
