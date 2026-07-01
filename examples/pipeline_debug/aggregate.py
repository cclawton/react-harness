"""Stage 3: group events by key and compute summaries."""


def aggregate_events(events, group_key):
    """Group events by the value of group_key.

    Returns a list of dicts sorted by key, each with:
    key, count, total_amount_aud, avg_amount_aud
    """
    groups = {}
    for event in events:
        key = event.get(group_key)
        if key not in groups:
            groups[key] = {"count": 0, "total_amount_aud": 0.0}
        groups[key]["count"] += 1
        groups[key]["total_amount_aud"] += float(event.get("amount_aud", 0.0))

    result = []
    for key in sorted(groups.keys()):
        count = groups[key]["count"]
        total = groups[key]["total_amount_aud"]
        result.append({
            "key": key,
            "count": count,
            "total_amount_aud": total,
            "avg_amount_aud": total / count if count else 0.0,
        })
    return result
