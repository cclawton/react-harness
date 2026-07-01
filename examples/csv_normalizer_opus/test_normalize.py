"""Tests for the CSV normalizer — do not modify this file."""
import csv
import os
import pytest


def run_normalizer():
    """Run the normalizer script and return the output path."""
    import subprocess
    result = subprocess.run(
        ["python", "normalize.py", "input.csv", "output.csv"],
        capture_output=True, text=True, cwd=os.getcwd(),
        timeout=30,
    )
    assert result.returncode == 0, f"normalizer failed: {result.stderr}"
    return "output.csv"


def read_csv(path):
    with open(path) as f:
        reader = csv.DictReader(f)
        return list(reader)


@pytest.fixture(scope="module")
def output_rows():
    path = run_normalizer()
    return read_csv(path)


class TestOutputExists:
    def test_output_file_created(self):
        path = run_normalizer()
        assert os.path.exists(path), "output.csv was not created"


class TestHeaders:
    def test_normalized_headers(self, output_rows):
        assert len(output_rows) > 0
        expected_headers = {"date", "product", "amount", "category", "notes"}
        assert set(output_rows[0].keys()) == expected_headers


class TestCategoryNormalized:
    def test_categories_are_lowercase(self, output_rows):
        for row in output_rows:
            assert row["category"] == row["category"].lower()
            assert row["category"] != row["category"].upper() or row["category"] == row["category"].lower()

    def test_categories_are_stripped(self, output_rows):
        for row in output_rows:
            assert row["category"] == row["category"].strip()

    def test_electronics_category(self, output_rows):
        cats = {r["category"] for r in output_rows}
        assert "electronics" in cats
        assert "ELECTRONICS" not in cats
        assert "Electronics" not in cats


class TestNotesStripped:
    def test_notes_have_no_leading_trailing_whitespace(self, output_rows):
        for row in output_rows:
            if row["notes"]:
                assert row["notes"] == row["notes"].strip()

    def test_empty_notes_are_empty_string(self, output_rows):
        for row in output_rows:
            if not row["notes"].strip():
                assert row["notes"] == ""


class TestAmountFormatted:
    def test_amounts_are_floats_with_two_decimals(self, output_rows):
        for row in output_rows:
            amount = row["amount"]
            # Should be parseable as float
            val = float(amount)
            # Should have exactly 2 decimal places
            assert "." in amount
            assert len(amount.split(".")[1]) == 2


class TestRowCount:
    def test_same_number_of_rows(self, output_rows):
        """Output should have the same number of data rows as input."""
        assert len(output_rows) == 8


class TestDateUnchanged:
    def test_dates_preserved(self, output_rows):
        dates = [r["date"] for r in output_rows]
        expected = [
            "2026-01-15", "2026-01-16", "2026-01-17", "2026-01-18",
            "2026-01-19", "2026-01-20", "2026-01-21", "2026-01-22",
        ]
        assert dates == expected
