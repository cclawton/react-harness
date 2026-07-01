from filter import filter_events
from enrich import enrich_events
from aggregate import aggregate_events
from report import generate_report


class PipelineError(Exception):
    pass


def run_pipeline(events, event_types, start_time, end_time, group_key):
    try:
        filtered = filter_events(events, event_types, start_time, end_time)
        enriched = enrich_events(filtered)
        aggregated = aggregate_events(enriched, group_key)
        return generate_report(aggregated)
    except PipelineError:
        raise
    except Exception as exc:
        raise PipelineError(str(exc)) from exc
