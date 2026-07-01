"""Entry point: chains filter → enrich → aggregate → report."""

from filter import filter_events
from enrich import enrich_events
from aggregate import aggregate_events
from report import generate_report


class PipelineError(Exception):
    """Raised when the pipeline encounters an error."""
    pass


def run_pipeline(events, event_types, start_time, end_time, group_key):
    """Run the full four-stage pipeline.

    Args:
        events: list of event dicts.
        event_types: list of types to keep, or None for all.
        start_time: ISO-8601 inclusive lower bound, or None.
        end_time: ISO-8601 exclusive upper bound, or None.
        group_key: key to group events by in aggregation.

    Returns:
        Report dict from generate_report.
    """
    filtered = filter_events(events, event_types, start_time, end_time)
    enriched = enrich_events(filtered)
    aggregated = aggregate_events(enriched, group_key)
    return generate_report(aggregated)
