"""Stage 1: filter events by type and/or time range."""


def filter_events(events, event_types, start_time, end_time):
    """Filter events by type and/or time range.

    Args:
        events: list of event dicts with at least 'type' and 'timestamp' keys.
        event_types: list of types to keep, or None to keep all types.
        start_time: ISO-8601 string (inclusive), or None for no lower bound.
        end_time: ISO-8601 string (exclusive), or None for no upper bound.

    Returns:
        list of event dicts preserving chronological order.
    """
    result = []
    for event in events:
        # Type filter
        if event_types is not None and event.get("type") not in event_types:
            continue
        # Time filter
        ts = event.get("timestamp")
        if start_time is not None and ts < start_time:
            continue
        if end_time is not None and ts >= end_time:
            continue
        result.append(event)
    return result
