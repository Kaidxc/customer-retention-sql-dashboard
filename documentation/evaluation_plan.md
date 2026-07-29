# Evaluation Plan

## Decision to evaluate

The analysis recommends prioritising high-value inactive customers for a retention campaign. That recommendation is a hypothesis: these customers look like a strong priority, but historical transaction data alone cannot prove that contacting them will cause additional purchases.

## Evaluation question

Does a targeted retention campaign improve repeat purchase behaviour among high-value inactive customers compared with a similar group that is not contacted during the same measurement window?

## Suggested design

| Element | Recommendation |
|---|---|
| Eligible population | Customers in the `At Risk High Value` segment with at least two previous orders. |
| Assignment | Randomly split eligible customers into treatment and control groups. |
| Treatment group | Receive the retention campaign. |
| Control group | Do not receive the campaign during the test window. |
| Measurement window | A fixed post-campaign window, for example 30, 60 or 90 days. |
| Primary metric | Repeat purchase rate during the measurement window. |
| Secondary metrics | Revenue per customer, average order value and number of orders per customer. |
| Guardrail metrics | Opt-outs, contact failures, complaint rate and campaign cost if available. |

## Success criteria

The campaign should be considered successful only if the treatment group performs better than the control group on repeat purchase rate and the difference is commercially meaningful after considering campaign cost.

## What this prevents

This evaluation design avoids treating correlation as proof. Customers with high historical value may have returned anyway. A control group helps estimate the incremental effect of the campaign rather than only reporting post-campaign revenue.

## Limitations

- Margin and campaign cost are not available in the current dataset, so the first analysis uses revenue rather than profit.
- Channel permissions and contact history are not available, so the project cannot check who can legally or practically be contacted.
- The sample size of the eligible group should be checked before committing to a final test design.
- Seasonality may affect results, so treatment and control groups should be measured over the same calendar period.

## Transferable value

This plan is relevant to any role where an analyst needs to evaluate whether an action worked. The same logic can be applied to service interventions, operational changes, communications campaigns, prevention activity, process improvements or customer programmes.
