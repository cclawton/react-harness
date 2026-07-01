"""Tests for the JSON parser — do not modify this file."""
import pytest
from parser import parse_json, ParseError


class TestPrimitives:
    def test_integer(self):
        assert parse_json("42") == 42

    def test_negative_integer(self):
        assert parse_json("-17") == -17

    def test_float(self):
        assert parse_json("3.14") == 3.14

    def test_negative_float(self):
        assert parse_json("-2.5") == -2.5

    def test_boolean_true(self):
        assert parse_json("true") is True

    def test_boolean_false(self):
        assert parse_json("false") is False

    def test_null(self):
        assert parse_json("null") is None

    def test_empty_string(self):
        assert parse_json('""') == ""


class TestStrings:
    def test_simple_string(self):
        assert parse_json('"hello"') == "hello"

    def test_string_with_spaces(self):
        assert parse_json('"hello world"') == "hello world"

    def test_escaped_quotes(self):
        assert parse_json('"say \\"hi\\""') == 'say "hi"'

    def test_escaped_backslash(self):
        assert parse_json('"path\\\\to"') == "path\\to"

    def test_escaped_newline(self):
        assert parse_json('"line1\\nline2"') == "line1\nline2"

    def test_unicode_string(self):
        assert parse_json('"caf\\u00e9"') == "café"


class TestArrays:
    def test_empty_array(self):
        assert parse_json("[]") == []

    def test_simple_array(self):
        assert parse_json("[1, 2, 3]") == [1, 2, 3]

    def test_mixed_array(self):
        assert parse_json('[1, "two", true, null]') == [1, "two", True, None]

    def test_nested_arrays(self):
        assert parse_json("[[1, 2], [3, 4]]") == [[1, 2], [3, 4]]

    def test_array_with_whitespace(self):
        assert parse_json("[ 1 , 2 , 3 ]") == [1, 2, 3]


class TestObjects:
    def test_empty_object(self):
        assert parse_json("{}") == {}

    def test_simple_object(self):
        assert parse_json('{"a": 1}') == {"a": 1}

    def test_multiple_keys(self):
        result = parse_json('{"a": 1, "b": 2, "c": 3}')
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_nested_object(self):
        assert parse_json('{"outer": {"inner": 42}}') == {"outer": {"inner": 42}}

    def test_mixed_object(self):
        result = parse_json('{"name": "test", "values": [1, 2], "active": true}')
        assert result == {"name": "test", "values": [1, 2], "active": True}


class TestComplexNesting:
    def test_deeply_nested(self):
        json_str = '{"a": {"b": {"c": {"d": [1, 2, 3]}}}}'
        assert parse_json(json_str) == {"a": {"b": {"c": {"d": [1, 2, 3]}}}}

    def test_array_of_objects(self):
        json_str = '[{"x": 1}, {"y": 2}]'
        assert parse_json(json_str) == [{"x": 1}, {"y": 2}]

    def test_object_with_array_values(self):
        json_str = '{"matrix": [[1, 0], [0, 1]]}'
        assert parse_json(json_str) == {"matrix": [[1, 0], [0, 1]]}


class TestWhitespace:
    def test_leading_whitespace(self):
        assert parse_json("  42") == 42

    def test_trailing_whitespace(self):
        assert parse_json('42  ') == 42

    def test_whitespace_in_object(self):
        assert parse_json('{ "a" : 1 }') == {"a": 1}

    def test_newlines_in_array(self):
        assert parse_json("[\n  1,\n  2\n]") == [1, 2]


class TestErrors:
    def test_unterminated_string(self):
        with pytest.raises(ParseError):
            parse_json('"hello')

    def test_unterminated_array(self):
        with pytest.raises(ParseError):
            parse_json("[1, 2")

    def test_unterminated_object(self):
        with pytest.raises(ParseError):
            parse_json('{"a": 1')

    def test_trailing_comma_in_array(self):
        with pytest.raises(ParseError):
            parse_json("[1, 2,]")

    def test_trailing_comma_in_object(self):
        with pytest.raises(ParseError):
            parse_json('{"a": 1,}')

    def test_empty_input(self):
        with pytest.raises(ParseError):
            parse_json("")

    def test_invalid_token(self):
        with pytest.raises(ParseError):
            parse_json("xyz")

    def test_double_comma(self):
        with pytest.raises(ParseError):
            parse_json("[1,,2]")
