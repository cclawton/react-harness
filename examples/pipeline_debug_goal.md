# Data Processing Pipeline — Cascading Error Task

The working directory contains a test file (`test_pipeline.py`) with 40+ tests for a four-stage data processing pipeline.

Your task:
1. Read `test_pipeline.py` carefully — understand the interfaces between stages
2. Create FIVE Python files:
   - `filter.py` — Stage 1: `filter_events(events, event_types, start_time, end_time) -> list[dict]`
     Filters events by type and/or time range. Times are ISO-8601 strings. Start is inclusive, end is exclusive. If event_types is None, keep all types. If start/end is None, no time filtering. Preserve chronological order.
   - `enrich.py` — Stage 2: `enrich_events(events) -> list[dict]`
     Adds three fields to each event:
     - `category`: "revenue" if amount > 0, "engagement" otherwise
     - `amount_aud`: amount converted to AUD. Fixed rates: AUD=1.0, USD=1.52, EUR=1.65
     - `hour`: the hour part extracted from timestamp (e.g. "10" from "2026-07-01T10:00:00Z")
     Must preserve all original fields.
   - `aggregate.py` — Stage 3: `aggregate_events(events, group_key) -> list[dict]`
     Groups events by the value of group_key. Returns list of dicts sorted by key, each with:
     `key`, `count`, `total_amount_aud`, `avg_amount_aud`
   - `report.py` — Stage 4: `generate_report(aggregated) -> dict`
     Returns a dict with:
     - `summary`: {total_events, total_revenue_aud, unique_groups}
     - `groups`: list sorted by total_amount_aud DESCENDING, each with all aggregate fields plus `percentage_of_revenue` (share of total revenue, 0-100)
   - `pipeline.py` — Entry point: `run_pipeline(events, event_types, start_time, end_time, group_key) -> dict`
     Chains: filter → enrich → aggregate → report. Also exports `PipelineError`.
3. Run the tests (`python -m pytest test_pipeline.py -v`) to verify
4. Signal done when all tests pass

Do NOT modify `test_pipeline.py`.

IMPORTANT: This task is designed to surface cascading errors. The test failures will often point at a later stage (e.g. report or aggregate), but the root cause may be in an earlier stage (e.g. enrich producing the wrong field name or format). When tests fail, trace the data flow through the pipeline — do not just fix the file that's failing. Check what each stage is actually producing before fixing the next one.

The interfaces between files are the hard part. If enrich produces `amount_aud` as a string instead of a float, aggregate's sum will fail. If filter returns events in the wrong order, aggregate's sorted output will be wrong. If aggregate uses a different key name than what report expects, the report will be missing fields. Trace the data, find the real cause, fix it at the source.
