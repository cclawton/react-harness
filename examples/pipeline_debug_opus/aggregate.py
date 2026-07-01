def aggregate_events(events, group_key):
    groups = {}
    for e in events:
        key = e[group_key]
        groups.setdefault(key, []).append(e)
    result = []
    for key in sorted(groups.keys()):
        items = groups[key]
        count = len(items)
        total = sum(item["amount_aud"] for item in items)
        avg = total / count if count else 0.0
        result.append({
            "key": key,
            "count": count,
            "total_amount_aud": total,
            "avg_amount_aud": avg,
        })
    return result
