"""Stage 4: format aggregated data into a structured report."""


def generate_report(aggregated):
    """Generate a report from aggregated data.

    Returns a dict with:
    - summary: {total_events, total_revenue_aud, unique_groups}
    - groups: list sorted by total_amount_aud descending, each with
      key, count, total_amount_aud, avg_amount_aud, percentage_of_revenue
    """
    total_events = sum(g["count"] for g in aggregated)
    total_revenue = sum(g["total_amount_aud"] for g in aggregated)
    unique_groups = len(aggregated)

    groups = []
    for g in aggregated:
        pct = (g["total_amount_aud"] / total_revenue * 100.0) if total_revenue else 0.0
        group = {
            "key": g["key"],
            "count": g["count"],
            "total_amount_aud": g["total_amount_aud"],
            "avg_amount_aud": g["avg_amount_aud"],
            "percentage_of_revenue": pct,
        }
        groups.append(group)

    groups.sort(key=lambda x: x["total_amount_aud"], reverse=True)

    return {
        "summary": {
            "total_events": total_events,
            "total_revenue_aud": total_revenue,
            "unique_groups": unique_groups,
        },
        "groups": groups,
    }
