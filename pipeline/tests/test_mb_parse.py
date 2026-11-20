import pathlib
import mb_parse

FX = pathlib.Path(__file__).parent / "fixtures"


def read(name):
    return (FX / name).read_text(encoding="utf-8", errors="ignore")


def test_list_page():
    h = read("mb_list.html")
    cards = mb_parse.parse_list_page(h)
    assert len(cards) == 20
    assert mb_parse.parse_total(h) == 2708
    p = mb_parse.card_to_project(cards[0])
    assert p["name"] == "Solutrean Gateway95"
    assert p["url"].startswith("https://www.magicbricks.com/solutrean-gateway95")


def test_plot_project_page():
    d = mb_parse.parse_project_page(read("mb_project_plot.html"))
    assert round(d["lat"], 5) == 28.41698 and round(d["lng"], 5) == 76.90962
    assert d["rera_id"].startswith("GGM/607")
    assert "Outdoor Tennis Courts" in d["amenities"]


def test_flat_project_page():
    d = mb_parse.parse_project_page(read("mb_project_flat.html"))
    assert d["towers"] == 27 and d["units"] == 1356
    assert d["config_text"] == "2, 3, 4 BHK Multistorey Apartments"
    sizes = sorted((u["bhk"], u["sqft"]) for u in d["configs"]["units"])
    assert (4, 2740.0) in sizes and (2, 1296.0) in sizes
    assert d["configs"]["by_bhk"][3]["plan_images"][0].endswith(".jpg")


def test_card_units_and_type_codes():
    cards = {c["psmName"]: c for c in mb_parse.parse_list_page(read("mb_list.html"))}
    p = mb_parse.card_to_project(cards["Ganga Anantam"])
    assert p["card_units"][0] == {"bhk": 3, "sqft": 2050.0, "kind": "10002"}
    assert p["type_codes"] == ["10002"]


def test_extras_ratings_reviews_listings():
    d = mb_parse.parse_project_page(read("mb_project_flat.html"))
    assert d["rating"] == 4.5 and d["review_count"] == 18 and d["ratings"]["maintenance"] == 4.7
    assert d["sale_count"] == 140 and d["rent_count"] == 27
    assert d["rent_listings"][0] == {"bhk": 2, "price": 45000.0, "sqft": 1296.0, "psf": 35.0, "furnished": "Semi-Furnished", "floor": "5", "posted": "2026-10-15"}
    assert d["sale_listings"][0]["price"] == 24000000
    assert d["psf_now"] == 16623 and d["trend"][0] == ["2021", 7567]
    assert d["reviews"][0]["text"].startswith("Ireo The Corridors is a thoughtfully")


def test_reviews_are_unique():
    d = mb_parse.parse_project_page(read("mb_project_flat.html"))
    keys = [r["text"][:60] for r in d["reviews"]]
    assert len(keys) == len(set(keys))


def test_photo_links_skip_floor_plans():
    links = mb_parse.photo_links("2025/09/18/Project-Photo-9-X-5021659_410_1440.jpg,2025/07/01/Floor-Plan-36-X_505_661.jpg")
    assert links == [{"thumb": "https://img.staticmb.com/mbimages/project/Photo_h310_w462/2025/09/18/Project-Photo-9-X-5021659_410_1440_310_462.jpg",
                      "full": "https://img.staticmb.com/mbimages/project/2025/09/18/Project-Photo-9-X-5021659_410_1440.jpg"}]
