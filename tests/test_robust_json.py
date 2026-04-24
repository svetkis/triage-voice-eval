"""Tests for robust JSON parser."""

from triage_voice_eval.parsing import parse


def test_valid_json():
    result, is_fallback = parse('{"key": "value"}')
    assert result == {"key": "value"}
    assert is_fallback is False


def test_markdown_wrapped():
    text = '```json\n{"key": "value"}\n```'
    result, fb = parse(text)
    assert result == {"key": "value"}
    assert fb is False


def test_markdown_no_language():
    text = '```\n{"key": "value"}\n```'
    result, fb = parse(text)
    assert result == {"key": "value"}
    assert fb is False


def test_json_in_surrounding_text():
    text = 'Here is the result:\n{"key": "value"}\nDone.'
    result, fb = parse(text)
    assert result == {"key": "value"}
    assert fb is False


def test_nested_objects():
    text = '{"outer": {"inner": [1, 2, 3]}}'
    result, fb = parse(text)
    assert result["outer"]["inner"] == [1, 2, 3]


def test_braces_in_strings():
    text = '{"msg": "use {name} placeholder"}'
    result, fb = parse(text)
    assert result["msg"] == "use {name} placeholder"


def test_truncated_json_missing_closing():
    text = '{"key": "value", "nested": {"a": 1'
    result, fb = parse(text)
    assert result["key"] == "value"
    assert fb is False


def test_truncated_json_mid_string():
    text = '{"key": "val'
    result, fb = parse(text)
    assert result["key"].startswith("val")
    assert fb is False


def test_truncated_json_mid_array():
    text = '{"items": [1, 2, 3'
    result, fb = parse(text)
    assert result["items"] == [1, 2, 3]
    assert fb is False


def test_complete_garbage():
    result, fb = parse("this is not json at all")
    assert fb is True
    assert result == {}


def test_custom_fallback():
    result, fb = parse("garbage", fallback={"fallback": True})
    assert result == {"fallback": True}
    assert fb is True


def test_escaped_quotes():
    text = '{"msg": "he said \\"hello\\""}'
    result, fb = parse(text)
    assert "hello" in result["msg"]


# Regression test for the hazard called out in robust_json.parse's docstring — a truncated advice string is truthy and would fool CrisisGuard into a spurious LEAK. Callers must check is_fallback OR validate field semantics before trusting such values.
def test_truncation_produces_truthy_but_partial_string_value():
    text = '{"is_crisis": true, "advice": "Call 911 imme'
    result, is_fallback = parse(text)
    assert "advice" in result
    assert isinstance(result["advice"], str)
    assert result["advice"]  # non-empty → truthy
    assert result["advice"].startswith("Call 911 imme")
    assert is_fallback is False
