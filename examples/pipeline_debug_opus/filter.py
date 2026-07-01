def filter_events(events, event_types, start_time, end_time):
    result = []
    for e in events:
        if event_types is not None and e["type"] not in event_types:
            continue
        ts = e["timestamp"]
        if start_time is not None and ts < start_time:
            continue
        if end_time is not None and ts >= end_time:
            continue
        result.append(e)
    return result
