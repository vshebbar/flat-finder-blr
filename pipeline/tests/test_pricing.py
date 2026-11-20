import pricing


def soc(loc, prices):
    return {"locality": loc, "prices": prices}


def test_listing_stats_median_per_bhk():
    p = {"sale_listings": [{"bhk": 3, "price": 2e7, "psf": 10000}, {"bhk": 3, "price": 3e7, "psf": 12000}, {"bhk": 2, "price": 1e7}],
         "rent_listings": [{"bhk": 3, "price": 60000}]}
    st = pricing.listing_stats(p)
    assert st[3]["buy"] == {"median": 25000000, "min": 20000000, "max": 30000000, "n": 2}
    assert st[3]["psf"] == 11000 and st[3]["rent"]["median"] == 60000 and "rent" not in st[2]


def test_yield_model_drops_mistakes_and_uses_locality():
    socs = [soc("Sector 62", {3: {"buy": {"median": 3e7}, "rent": {"median": 75000}}}) for _ in range(4)]
    socs.append(soc("Sector 62", {3: {"buy": {"median": 3e7}, "rent": {"median": 900000}}}))  # yearly typed as monthly
    m = pricing.fit_yields(socs)
    assert m["pairs"] == 4 and m["locality_yield"]["Sector 62"] == 0.03


def test_estimates_are_labelled_and_never_replace_listings():
    m = {"city_yield": 0.03, "bhk_yield": {}, "locality_yield": {}}
    s = soc("Sector 99", {3: {"buy": {"median": 2e7}}, 2: {"rent": {"median": 40000}}})
    pricing.add_estimates(s, m, {4: 3000}, psf_fallback=10000)
    assert s["prices"][3]["buy"]["median"] == 2e7 and s["prices"][3]["rent_est"]["value"] == 50000
    assert s["prices"][2]["buy_est"]["value"] == 16000000 and "rent" in s["prices"][2]["buy_est"]["basis"]
    assert s["prices"][4]["buy_est"]["value"] == 30000000 and s["prices"][4]["rent_est"]["value"] == 75000


def test_flags_typos_but_keeps_values_and_skips_them_for_estimates():
    socs = [soc("Sector 57", {3: {"buy": {"median": 4e7, "min": 4e7, "max": 4e7, "n": 2}, "rent": {"median": 90000, "min": 90000, "max": 90000, "n": 1}}}) for _ in range(5)]
    bad = soc("Sector 57", {3: {"buy": {"median": 4.1e7, "min": 3.7e7, "max": 3.9e8, "n": 4}, "rent": {"median": 960000, "min": 960000, "max": 960000, "n": 1}}})
    socs.append(bad)
    assert pricing.flag_outliers(socs) == 1
    p = bad["prices"][3]
    assert p["rent"]["median"] == 960000 and "16" not in p["flags"]["rent"] and "10.7x" in p["flags"]["rent"]
    assert "buy_range" in p["flags"] and "buy" not in p["flags"]
    pricing.add_estimates(bad, {"city_yield": 0.03, "bhk_yield": {}, "locality_yield": {}}, {}, None)
    assert p["rent_est"]["value"] == 102500  # estimated from the price, ignoring the flagged rent


def test_luxury_price_backed_by_builder_range_is_not_flagged():
    socs = [soc("Sector 65", {4: {"buy": {"median": 3e7, "min": 3e7, "max": 3e7, "n": 1}}}) for _ in range(5)]
    lux = soc("Sector 65", {4: {"buy": {"median": 3e8, "min": 3e8, "max": 3e8, "n": 1}}})
    lux["price_min"], lux["price_max"] = 2e8, 4e8
    socs.append(lux)
    assert pricing.flag_outliers(socs) == 0
