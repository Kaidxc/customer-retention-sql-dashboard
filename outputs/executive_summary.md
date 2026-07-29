# Executive Summary

## Objective

Identify which existing customers should be prioritised for a retention campaign when marketing budget is limited.

## Dataset

- Analysis date: 2011-12-10
- Clean transaction rows: 793,609
- Distinct customers: 5,878
- Distinct orders: 36,969
- Total clean revenue: GBP 17,685,461

## Key findings

- Repeat purchase rate across known customers is 72.4%.
- The highest revenue RFM segment is `Champions`, contributing GBP 12,156,257.
- `397` customers are classified as `At Risk High Value`, representing GBP 1,465,866 in historical revenue.
- The campaign target list contains `300` customers prioritised by historical value, order frequency, and inactivity.
- Average month 1 to 3 cohort retention is 21.6%.
- Data quality checks passed: 6/6.
- Next-month revenue baseline forecast: GBP 903,019 for 2012-01-01.

## Recommended CRM action

Prioritise the `At Risk High Value` segment first. These customers have meaningful historical spend but have not purchased recently, making them better candidates for a targeted retention campaign than low-value inactive customers.

## Evidence for decision-makers

- [Segment revenue view](../documentation/figures/segment_revenue.svg) shows where historical value is concentrated and highlights the retention opportunity.
- [Monthly KPI trend](../documentation/figures/monthly_kpis.svg) shows how revenue and monthly repeat purchasing change over time.
- [Monthly forecast baseline](../documentation/figures/monthly_forecast.svg) shows a transparent short-term revenue planning baseline.
- [Cohort retention heatmap](../documentation/figures/cohort_retention.svg) shows the drop-off in repeat purchasing after the first purchase month.
- [Campaign decision funnel](../documentation/figures/campaign_funnel.svg) shows how the campaign scope narrows from the full customer base to a testable target list.

## Measurement recommendation

Run an A/B test on the campaign target list. Randomly assign eligible customers into treatment and control groups, then compare repeat purchase rate, revenue per customer, and average order value over a fixed measurement window.

## Forecasting note

The forecasting extension uses a transparent 3-month moving average baseline for short-term planning. This is useful for trend interpretation, but should not be treated as a production forecasting model without additional validation and business context.
