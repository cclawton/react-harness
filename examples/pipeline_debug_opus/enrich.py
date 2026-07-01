RATES = {"AUD": 1.0, "USD": 1.52, "EUR": 1.65}


def enrich_events(events):
    result = []
    for e in events:
        new = dict(e)
        amount = e["amount"]
        new["category"] = "revenue" if amount > 0 else "engagement"
        rate = RATES[e["currency"]]
        new["amount_aud"] = float(amount) * rate
        ts = e["timestamp"]
        hour_part = ts.split("T")[1].split(":")[0]
        new["hour"] = str(int(hour_part))
        result.append(new)
    return result
