import jev_reader as j


def lad(prefix, steps, vals):
    return {f"{prefix}_{x}": {"noul": v} for x, v in zip(steps, vals)}


def test_bounds_take_the_confirmed_run_only():
    steps = [11, 11.5, 12, 12.5, 13]
    assert j.bounds(lad("long", steps, [0.91, 0.81, 0.76, 0.36, 0.37]), "long", steps) == (12, None)
    assert j.bounds(lad("long", steps, [0.9, 0.81, 0.81, 0.5, 0.69]), "long", steps) == (12, None)
    assert j.bounds(lad("long", steps, [0.9, 0.2, 0.9, 0.9, 0.9]), "long", steps) == (11, 11.5)


def test_bounds_nothing_confirmed():
    steps = [11, 12]
    assert j.bounds(lad("area", steps, [0.5, 0.2]), "area", steps) == (None, 12)


def test_option_round_trip():
    assert j.option_ft("f10i6") == 10.5
    assert list(j.options(10, 10.5)) == ["f10i0", "f10i3", "f10i6"]
