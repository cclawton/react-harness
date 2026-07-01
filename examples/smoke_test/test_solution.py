"""Tests for the smoke test — do not modify this file."""
import pytest
from solution import is_prime


@pytest.mark.parametrize("n,expected", [
    (0, False),
    (1, False),
    (2, True),
    (3, True),
    (4, False),
    (5, True),
    (10, False),
    (11, True),
    (13, True),
    (97, True),
    (100, False),
    (-5, False),
    (-1, False),
])
def test_is_prime(n, expected):
    assert is_prime(n) == expected
