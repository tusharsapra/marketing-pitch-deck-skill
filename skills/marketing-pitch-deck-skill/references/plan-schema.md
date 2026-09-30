# Deck blueprint schema

Use the blank asset as a starting point. Its empty fields intentionally fail validation until filled. The repository's `examples/sample-plan.json` demonstrates filled syntax with fictional data; it is not a recommendation or market benchmark.

## Top-level fields

| Field | Required structure |
| --- | --- |
| metadata | brand, objective, audience, primary_outcome; optional positive expected_slide_count, currency and budget_basis |
| sources | Array of objects: unique id, label, url or file; add publication_date, data_period, geography, source_type and limitation |
| claims | Array: unique id, statement, evidence_type, source_ids; basis for directional/assumption/proposed claims |
| slides | Array in presentation order; at least one object |
| scenarios | Array: unique id and media_budget, measured in metadata currency; add non-media costs separately |
| media_lines | Array of forecast lines linked to a scenario; spend uses the same media cost basis |

Use empty arrays for scenarios/media_lines when this deck has no numerical media plan. Source and asset file paths refer to the working project, not the installed skill. IDs must be stable nonempty strings.

## Claims and slides

Use evidence types `verified`, `supplied`, `directional`, `assumption` or `proposed`. Verified and supplied claims need source IDs. The other types need a basis describing the inference, planning input or proposal. All referenced IDs must exist.

Each slide needs id, chapter, purpose, reader_question, title, takeaway, body (string array), claim_ids (string array), visual (object with type and optional asset_refs string array), disclosures (string array) and transition. Add notes, metric_definitions, dependencies and revision_lock where relevant.

For directional, assumption and proposed claims, disclosures must contain the actual wording intended to appear visibly on that slide. The validator checks presence, not whether wording is accurate or whether every claim is truly disclosed. Cover/setup slides can have no claim IDs. The expected slide count includes cover and appendix unless the brief says otherwise.

## Media lines

Required fields: id, scenario_id, spend and cost_model. Add partner, role, source/basis, confirmation_status and metric_definition to preserve interpretation.

| cost_model | Required rate and forecast field |
| --- | --- |
| CPM | Positive rate per thousand impressions; impressions |
| CPV | Positive rate per defined view; views |
| CPC | Positive rate per click; clicks |
| CPA | Positive rate per defined outcome; conversions |
| FIXED | Nonnegative spend; no rate-derived forecast is assumed |

Optional ctr and cvr use fractions, e.g. 0.01 for 1%. If clicks, impressions and ctr are provided, the validator checks their relationship. It likewise checks conversions, clicks and cvr. Optional average_frequency requires impressions, positive unique_reach and identical nonempty impression_scope/reach_scope. Matching scope strings declare comparability; a human must substantiate it. Do not combine overlapping reach across lines without a deduplication method.

For money and delivery counts, the utility accepts rounding differences up to the greater of 0.5 units or 0.5% of the expected value. For average frequency, the absolute tolerance is 0.01 rather than 0.5. Check whether the tolerances are appropriate for the actual model. Media-line spend must sum to each scenario's media_budget. Production, fees and tax remain outside that total unless included consistently in the declared spend basis; reconcile total campaign costs separately.

Do not treat a clean validator result as confirmation of source accuracy, realistic inventory/rates, strategic quality, mathematically sound reach deduplication or presentation design.
