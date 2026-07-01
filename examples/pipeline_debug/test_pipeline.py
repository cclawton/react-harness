"""Tests for the data processing pipeline — do not modify this file.

This test suite tests a four-stage pipeline that processes event records.
Each stage is in its own file:

  filter.py    — Stage 1: filters events by type and time range
  enrich.py    — Stage 2: enriches events with metadata
  aggregate.py — Stage 3: groups events by key and computes summaries
  report.py    — Stage 4: formats aggregated data into a structured report

The main entry point is pipeline.py which chains them together.

The pipeline processes event dicts that look like:
  {"id": "...", "type": "click|view|purchase", "timestamp": "ISO-8601",
   "user": "...", "amount": float, "currency": "AUD|USD|EUR"}
"""
import pytest
from pipeline import run_pipeline, PipelineError
from filter import filter_events
from enrich import enrich_events
from aggregate import aggregate_events
from report import generate_report


# --- Test data --------------------------------------------------------------

EVENTS = [
    {"id": "e1", "type": "click", "timestamp": "2026-07-01T10:00:00Z", "user": "alice", "amount": 0.0, "currency": "AUD"},
    {"id": "e2", "type": "view", "timestamp": "2026-07-01T10:05:00Z", "user": "alice", "amount": 0.0, "currency": "AUD"},
    {"id": "e3", "type": "purchase", "timestamp": "2026-07-01T10:10:00Z", "user": "bob", "amount": 50.00, "currency": "AUD"},
    {"id": "e4", "type": "click", "timestamp": "2026-07-01T11:00:00Z", "user": "bob", "amount": 0.0, "currency": "AUD"},
    {"id": "e5", "type": "purchase", "timestamp": "2026-07-01T11:30:00Z", "user": "charlie", "amount": 120.00, "currency": "USD"},
    {"id": "e6", "type": "view", "timestamp": "2026-07-01T09:00:00Z", "user": "alice", "amount": 0.0, "currency": "AUD"},
    {"id": "e7", "type": "purchase", "timestamp": "2026-07-01T12:00:00Z", "user": "bob", "amount": 75.50, "currency": "EUR"},
    {"id": "e8", "type": "click", "timestamp": "2026-07-01T12:15:00Z", "user": "charlie", "amount": 0.0, "currency": "USD"},
    {"id": "e9", "type": "purchase", "timestamp": "2026-07-01T12:30:00Z", "user": "alice", "amount": 200.00, "currency": "AUD"},
    {"id": "e10", "type": "view", "timestamp": "2026-07-01T13:00:00Z", "user": "bob", "amount": 0.0, "currency": "AUD"},
]


class TestFilterEvents:
    """Stage 1: filter_events(events, event_types, start_time, end_time)"""

    def test_filter_by_single_type(self):
        result = filter_events(EVENTS, ["purchase"], None, None)
        ids = [e["id"] for e in result]
        assert ids == ["e3", "e5", "e7", "e9"]

    def test_filter_by_multiple_types(self):
        result = filter_events(EVENTS, ["click", "view"], None, None)
        ids = [e["id"] for e in result]
        assert ids == ["e1", "e2", "e4", "e6", "e8", "e10"]

    def test_filter_by_time_range(self):
        result = filter_events(EVENTS, None, "2026-07-01T10:00:00Z", "2026-07-01T11:00:00Z")
        ids = [e["id"] for e in result]
        # Inclusive start, exclusive end: 10:00, 10:05, 10:10 (not 11:00)
        assert ids == ["e1", "e2", "e3"]

    def test_filter_by_type_and_time(self):
        result = filter_events(EVENTS, ["purchase"], "2026-07-01T10:00:00Z", "2026-07-01T12:00:00Z")
        ids = [e["id"] for e in result]
        # e3 (10:10), e5 (11:30) — not e7 (12:00, exclusive end)
        assert ids == ["e3", "e5"]

    def test_filter_preserves_order(self):
        result = filter_events(EVENTS, ["click"], None, None)
        timestamps = [e["timestamp"] for e in result]
        assert timestamps == sorted(timestamps)

    def test_filter_no_types_returns_all(self):
        result = filter_events(EVENTS, None, None, None)
        assert len(result) == len(EVENTS)

    def test_filter_empty_input(self):
        result = filter_events([], ["click"], None, None)
        assert result == []


class TestEnrichEvents:
    """Stage 2: enrich_events(events) — adds metadata to each event.

    Adds:
    - 'category': 'revenue' if amount > 0, 'engagement' otherwise
    - 'amount_aud': amount converted to AUD using fixed rates
    - 'hour': extracted from timestamp (e.g. '10' from '2026-07-01T10:00:00Z')
    """

    def test_enrich_adds_category(self):
        enriched = enrich_events(EVENTS[:3])
        assert enriched[0]["category"] == "engagement"  # click, amount 0
        assert enriched[1]["category"] == "engagement"  # view, amount 0
        assert enriched[2]["category"] == "revenue"      # purchase, amount 50

    def test_enrich_adds_amount_aud(self):
        enriched = enrich_events(EVENTS[:5])
        # e3: 50.00 AUD -> 50.00
        assert enriched[2]["amount_aud"] == pytest.approx(50.00)
        # e5: 120.00 USD -> 120 * 1.52 = 182.40
        assert enriched[4]["amount_aud"] == pytest.approx(182.40)

    def test_enrich_adds_hour(self):
        enriched = enrich_events(EVENTS[:3])
        assert enriched[0]["hour"] == "10"
        assert enriched[1]["hour"] == "10"
        assert enriched[2]["hour"] == "10"

    def test_enrich_preserves_original_fields(self):
        enriched = enrich_events(EVENTS[:1])
        assert enriched[0]["id"] == "e1"
        assert enriched[0]["type"] == "click"
        assert enriched[0]["user"] == "alice"
        assert enriched[0]["amount"] == 0.0
        assert enriched[0]["currency"] == "AUD"

    def test_enrich_eur_conversion(self):
        enriched = enrich_events([EVENTS[6]])  # e7: 75.50 EUR
        # EUR to AUD: 75.50 * 1.65 = 124.575
        assert enriched[0]["amount_aud"] == pytest.approx(124.575)

    def test_enrich_empty_input(self):
        assert enrich_events([]) == []


class TestAggregateEvents:
    """Stage 3: aggregate_events(events, group_key) — groups by key and computes summary.

    Returns a list of dicts with: key, count, total_amount_aud, avg_amount_aud
    """

    def test_aggregate_by_user(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "user")
        # Group by user
        users = {a["key"] for a in agg}
        assert users == {"alice", "bob", "charlie"}

    def test_aggregate_by_type(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "type")
        types = {a["key"] for a in agg}
        assert types == {"click", "view", "purchase"}

    def test_aggregate_by_hour(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "hour")
        hours = {a["key"] for a in agg}
        assert hours == {"9", "10", "11", "12", "13"}

    def test_aggregate_count(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "user")
        by_user = {a["key"]: a for a in agg}
        # alice: e1, e2, e6, e9 = 4 events
        assert by_user["alice"]["count"] == 4
        # bob: e3, e4, e7, e10 = 4 events
        assert by_user["bob"]["count"] == 4
        # charlie: e5, e8 = 2 events
        assert by_user["charlie"]["count"] == 2

    def test_aggregate_total_amount(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "user")
        by_user = {a["key"]: a for a in agg}
        # alice: e9 = 200.00 AUD
        assert by_user["alice"]["total_amount_aud"] == pytest.approx(200.00)
        # bob: e3 = 50.00 + e7 = 124.575 = 174.575
        assert by_user["bob"]["total_amount_aud"] == pytest.approx(174.575)
        # charlie: e5 = 182.40
        assert by_user["charlie"]["total_amount_aud"] == pytest.approx(182.40)

    def test_aggregate_avg_amount(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "user")
        by_user = {a["key"]: a for a in agg}
        # alice: 200.00 / 4 = 50.00
        assert by_user["alice"]["avg_amount_aud"] == pytest.approx(50.00)
        # bob: 174.575 / 4 = 43.64375
        assert by_user["bob"]["avg_amount_aud"] == pytest.approx(43.64375)

    def test_aggregate_sorted_by_key(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "user")
        keys = [a["key"] for a in agg]
        assert keys == sorted(keys)

    def test_aggregate_empty(self):
        assert aggregate_events([], "user") == []


class TestGenerateReport:
    """Stage 4: generate_report(aggregated) — formats into a structured report.

    Returns a dict with:
    - 'summary': {total_events, total_revenue_aud, unique_groups}
    - 'groups': list of dicts sorted by total_amount_aud descending
      each with: key, count, total_amount_aud, avg_amount_aud, percentage_of_revenue
    """

    def test_report_structure(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "user")
        report = generate_report(agg)
        assert "summary" in report
        assert "groups" in report

    def test_report_summary_total_events(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "user")
        report = generate_report(agg)
        assert report["summary"]["total_events"] == 10

    def test_report_summary_total_revenue(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "user")
        report = generate_report(agg)
        # 200.00 + 174.575 + 182.40 = 556.975
        assert report["summary"]["total_revenue_aud"] == pytest.approx(556.975)

    def test_report_summary_unique_groups(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "user")
        report = generate_report(agg)
        assert report["summary"]["unique_groups"] == 3

    def test_report_groups_sorted_by_revenue_desc(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "user")
        report = generate_report(agg)
        revenues = [g["total_amount_aud"] for g in report["groups"]]
        assert revenues == sorted(revenues, reverse=True)

    def test_report_groups_have_percentage(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "user")
        report = generate_report(agg)
        for g in report["groups"]:
            assert "percentage_of_revenue" in g
            pct = g["percentage_of_revenue"]
            assert 0.0 <= pct <= 100.0
        # alice has 200/556.975 = 35.91%
        alice = [g for g in report["groups"] if g["key"] == "alice"][0]
        assert alice["percentage_of_revenue"] == pytest.approx(35.91, abs=0.1)

    def test_report_group_fields(self):
        enriched = enrich_events(EVENTS)
        agg = aggregate_events(enriched, "user")
        report = generate_report(agg)
        g = report["groups"][0]
        assert "key" in g
        assert "count" in g
        assert "total_amount_aud" in g
        assert "avg_amount_aud" in g
        assert "percentage_of_revenue" in g

    def test_report_empty(self):
        report = generate_report([])
        assert report["summary"]["total_events"] == 0
        assert report["summary"]["total_revenue_aud"] == 0
        assert report["summary"]["unique_groups"] == 0
        assert report["groups"] == []


class TestFullPipeline:
    """End-to-end: run_pipeline(events, event_types, start_time, end_time, group_key)"""

    def test_pipeline_full_run(self):
        report = run_pipeline(EVENTS, None, None, None, "user")
        assert report["summary"]["total_events"] == 10
        assert report["summary"]["unique_groups"] == 3
        assert report["summary"]["total_revenue_aud"] == pytest.approx(556.975)

    def test_pipeline_filtered(self):
        report = run_pipeline(EVENTS, ["purchase"], None, None, "user")
        # Only purchase events: e3, e5, e7, e9
        assert report["summary"]["total_events"] == 4
        assert report["summary"]["unique_groups"] == 3  # bob, charlie, alice

    def test_pipeline_time_filtered(self):
        report = run_pipeline(EVENTS, None, "2026-07-01T10:00:00Z", "2026-07-01T12:00:00Z", "type")
        # Events from 10:00 to 12:00 (exclusive): e1, e2, e3, e4, e5, e8
        # Wait — e8 is at 12:15, that's outside. Let me recheck.
        # 10:00-12:00 exclusive: e1(10:00), e2(10:05), e3(10:10), e4(11:00), e5(11:30)
        # e7(12:00) is excluded (exclusive end)
        assert report["summary"]["total_events"] == 5

    def test_pipeline_group_by_hour(self):
        report = run_pipeline(EVENTS, None, None, None, "hour")
        hours = {g["key"] for g in report["groups"]}
        assert hours == {"9", "10", "11", "12", "13"}

    def test_pipeline_empty_input(self):
        report = run_pipeline([], None, None, None, "user")
        assert report["summary"]["total_events"] == 0
        assert report["groups"] == []

    def test_pipeline_preserves_filter_order(self):
        """Events should maintain chronological order through the pipeline."""
        report = run_pipeline(EVENTS, ["click"], None, None, "hour")
        # Clicks: e1(10:00), e4(11:00), e8(12:15)
        # Grouped by hour: 10 -> 1 event, 11 -> 1 event, 12 -> 1 event
        assert report["summary"]["total_events"] == 3

    def test_pipeline_revenue_percentage_sum(self):
        """Percentages should sum to approximately 100."""
        report = run_pipeline(EVENTS, ["purchase"], None, None, "user")
        total_pct = sum(g["percentage_of_revenue"] for g in report["groups"])
        assert total_pct == pytest.approx(100.0, abs=0.01)
