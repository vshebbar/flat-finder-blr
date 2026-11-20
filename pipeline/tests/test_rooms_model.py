import rooms_model


def unit(size, bhk, rooms):
    return {"super_sqft": size, "bhk": bhk, "bedrooms": rooms, "rooms_complete": True}


def test_lower_bound_never_above_any_verified_room():
    socs = [{"unit_types": [unit(1890, 3, [[11.0, 15.5], [11.25, 12.25], [11.0, 13.0]]), unit(4279, 4, [[12.17, 14.9], [12.83, 16.3]] * 2),
                            unit(1261, 2, [[10.0, 15.0], [10.0, 12.5]]), unit(2380, 3, [[11.08, 16.0], [11.0, 13.75], [10.5, 14.0]]),
                            unit(3677, 4, [[11.58, 16.0], [11.83, 14.0]] * 2), unit(1828, 3, [[12.5, 13.25], [11.0, 12.5], [10.83, 13.0]]),
                            unit(6171, 4, [[11.58, 16.83]] * 4), unit(1358, 2, [[10.83, 13.0], [10.83, 11.83]])]}]
    m = rooms_model.fit(socs)
    for u in socs[0]["unit_types"]:
        short, area = rooms_model.lower_bounds(m, u["super_sqft"], u["bhk"])
        assert short <= min(r[0] for r in u["bedrooms"]) + 1e-6
        assert area <= min(r[0] * r[1] for r in u["bedrooms"]) + 1e-6


def test_no_model_without_enough_data():
    assert rooms_model.fit([{"unit_types": []}]) is None
    assert rooms_model.lower_bounds(None, 2000, 3) is None
