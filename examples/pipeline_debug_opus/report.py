def generate_report(aggregated):
    total_events = sum(g["count"] for g in aggregated)
    total_revenue = sum(g["total_amount_aud"] for g in aggregated)
    unique_groups = len(aggregated)

    groups = []
    for g in aggregated:
        ng = dict(g)
        if total_revenue:
            ng["percentage_of_revenue"] = g["total_amount_aud"] / total_revenue * 100.0
        else:
            ng["percentage_of_revenue"] = 0.0
        groups.append(ng)
    groups.sort(key=lambda g: g["total_amount_aud"], reverse=True)

    return {
        "summary": {
            "total_events": total_events,
            "total_revenue_aud": total_revenue,
            "unique_groups": unique_groups,
        },
        "groups": groups,
    }
