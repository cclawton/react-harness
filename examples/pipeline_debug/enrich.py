"""Stage 2: enrich events with metadata."""

RATES = {"AUD": 1.0, "USD": 1.52, "EUR": 1.65}


def enrich_events(events):
    """Add category, amount_aud, and hour to each event.

    Preserves all original fields.
    """
    result = []
    for event in events:
        enriched = dict(event)
        amount = event.get("amount", 0.0)
        currency = event.get("currency", "AUD")
        enriched["category"] = "revenue" if amount > 0 else "engagement"
        enriched["amount_aud"] = float(amount) * RATES.get(currency, 1.0)
        # Extract hour from timestamp like "2026-07-01T10:00:00Z"
        ts = event.get("timestamp", "")
        # Format: YYYY-MM-DDTHH:MM:SSZ -> hour is chars at index 11-13
        hour = ts[11:13] if len(ts) >= 13 else ""
        # Strip leading zero so "09" becomes "9"
        if hour and hour.startswith("0"):
            hour = hour[1:]
        enriched["hour"] = hour
        result.append(enriched)
    return result
