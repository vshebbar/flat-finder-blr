import plan_ocr as p


def test_parse_size_formats():
    assert p.parse_size("12'-9\"Х11'-4\"") == (11.333, 12.75)       # Cyrillic X from OCR
    assert p.parse_size("11'-6\"X14-10*") == (11.5, 14.833)          # missing apostrophe, * for inch
    assert p.parse_size("3350 X 3700") == (10.991, 12.139)           # millimetres
    assert p.parse_size("4.72 X 4.19") == (13.747, 15.486)           # metres
    assert p.parse_size("11'0\" X 11'0\"") == (11.0, 11.0)
    assert p.parse_size("BALCONY 4' WIDE") is None
    assert p.parse_size("5'-9\"X7'-10\"") is None                    # too small for a bedroom side


def test_pairs_labels_with_sizes_below():
    boxes = [("BED ROOM 1", .60, .20, .02, 1), ("12'-9\"Х11'-4\"", .60, .22, .02, 1),
             ("BED ROOM 2", .59, .61, .02, 1), ("13'-1\"X11'-1\"", .59, .63, .02, 1),
             ("MASTER BED ROOM", .73, .77, .02, 1), ("11'-6\"X14-10*", .73, .79, .02, 1),
             ("TOILET-1", .52, .90, .02, 1), ("5'-9\"Х7'-10\"", .52, .92, .02, 1)]
    beds = p.bedrooms_from_boxes(boxes)
    assert len(beds) == 3
    assert min(b["ft"][0] for b in beds) == 11.083                  # 11'1": the room Jev missed


def test_judge_flags_disagreement_and_count():
    r = {"bedrooms": [{"ft": (11.083, 13.083)}, {"ft": (11.333, 12.75)}, {"ft": (11.5, 14.833)}], "bhk_listed": 3}
    assert p.judge(dict(r), {"bhk": 3, "min_short": 11.5})["status"] == "OCR and Jev disagree"
    assert p.judge(dict(r), {"bhk": 3, "min_short": 11.0})["status"] == "read"
    assert p.judge(dict(r, bhk_listed=4), None)["status"].startswith("found 3 bedrooms")


def test_toilet_size_never_lands_on_a_bedroom():
    boxes = [("Bedroom", .77, .74, .02, 1), ("11'11\"x13'11\"", .77, .76, .02, 1),
             ("Toilet", .88, .78, .02, 1), ("6'x8'4\"", .88, .80, .02, 1)]
    beds = p.bedrooms_from_boxes(boxes)
    assert [b["ft"] for b in beds] == [(11.917, 13.917)]


def test_size_table_rows():
    boxes = [("Master Bedroom", .70, .30, .015, 1), ("13'0\" x 15'0\"", .90, .30, .015, 1),
             ("Bedroom 2", .70, .33, .015, 1), ("11'0\" x 12'6\"", .90, .33, .015, 1),
             ("Kitchen", .70, .36, .015, 1), ("8'0\" x 10'0\"", .90, .36, .015, 1)]
    assert sorted(b["ft"] for b in p.bedrooms_from_boxes(boxes)) == [(11.0, 12.5), (13.0, 15.0)]
