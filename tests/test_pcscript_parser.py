from src.ng_pce.pcscript import parse_string
from src.ng_pce.pcscript.dataclasses import TupleValue


def test_tuple_assignments_are_parsed_as_tuple_values():
    parsed = parse_string("demo is scene:\n  scale: 1.2, 3.4\n")

    scene = parsed[0]
    value = scene.properties["scale"]

    assert isinstance(value, TupleValue)
    assert value.first == 1.2
    assert value.second == 3.4
    assert value == (1.2, 3.4)


def test_simple_scalar_assignments_still_parse():
    parsed = parse_string("demo is scene:\n  title: \"Hello\"\n")

    scene = parsed[0]
    assert scene.properties["title"] == "Hello"
