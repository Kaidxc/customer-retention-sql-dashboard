# Data Quality Checks

## Why this matters

The recommendation is only useful if the underlying data is reliable enough for customer-level prioritisation. This project therefore includes a lightweight quality-assurance layer before the insight is used for action.

The checks are framed around six common data quality dimensions:

| Dimension | What it checks in this project | Why it matters |
|---|---|---|
| Accuracy | Whether `line_value` matches `quantity * unit_price` | Revenue and customer value calculations depend on this. |
| Validity | Whether transaction values are positive and usable | Cancelled or invalid rows would distort customer KPIs. |
| Timeliness | Whether transaction dates sit within the analysis window | Recency and trend analysis rely on sensible dates. |
| Completeness | Whether key fields such as customer, invoice, date and value are populated | Missing IDs prevent customer-level targeting. |
| Consistency | Whether invoices map to a single customer | Inconsistent invoice ownership can affect order counts. |
| Uniqueness | Whether duplicate transaction lines remain | Duplicates can inflate revenue, frequency and segment value. |

## Generated output

The SQL check file is [`../sql/07_data_quality_checks.sql`](../sql/07_data_quality_checks.sql). It produces:

```text
outputs/data_quality_checks.csv
```

Each row records the dimension, check name, affected row count, affected share and status.

## How to read it

- `Pass` means the check found no affected rows in the cleaned analytical dataset.
- `Review` means the issue should be investigated before the output is used for a decision.
- A clean result does not mean the original raw data was perfect. It means the final analytical table passed the checks selected for this portfolio use case.

## Transferable value

The same approach can be used beyond retail customer analytics. For a performance, public service, BI or evaluation role, these checks translate into a habit of asking:

- Is the data complete enough to support the decision?
- Are the values valid and internally consistent?
- Are dates and records timely enough for planning?
- Could duplicates or missing identifiers change the conclusion?
- Are limitations visible to stakeholders before recommendations are made?
