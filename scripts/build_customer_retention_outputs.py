from __future__ import annotations

import html
import json
import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    PROJECT_ROOT.parent
    / "SQL_Study_package"
    / "day1_customer_retention_learning_pack"
    / "outputs"
    / "clean_transactions.csv"
)
SQL_DIR = PROJECT_ROOT / "sql"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"


QUERY_OUTPUTS = {
    "00_dataset_overview.sql": "dataset_overview.csv",
    "01_customer_kpis.sql": "customer_metrics.csv",
    "02_rfm_segmentation.sql": "rfm_segments.csv",
    "02b_rfm_segment_summary.sql": "rfm_segment_summary.csv",
    "03_cohort_retention.sql": "cohort_retention.csv",
    "04_campaign_targets.sql": "campaign_targets.csv",
    "05_monthly_kpis.sql": "monthly_kpis.csv",
}


def load_transactions(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Run the Day 1 cleaning script first or pass a cleaned CSV path."
        )

    dtypes = {
        "invoice_no": "string",
        "stock_code": "string",
        "description": "string",
        "customer_id": "string",
        "country": "string",
        "source_period": "string",
    }
    df = pd.read_csv(input_path, dtype=dtypes, parse_dates=["invoice_date"])
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["line_value"] = pd.to_numeric(df["line_value"], errors="coerce")
    df = df.dropna(subset=["invoice_no", "customer_id", "invoice_date", "line_value"])
    df["invoice_date"] = df["invoice_date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def create_database(df: pd.DataFrame) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    df.to_sql("clean_transactions", conn, index=False, if_exists="replace")
    conn.execute("CREATE INDEX idx_transactions_customer ON clean_transactions(customer_id)")
    conn.execute("CREATE INDEX idx_transactions_invoice ON clean_transactions(invoice_no)")
    conn.execute("CREATE INDEX idx_transactions_date ON clean_transactions(invoice_date)")
    return conn


def run_sql_outputs(conn: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, pd.DataFrame] = {}

    for sql_name, csv_name in QUERY_OUTPUTS.items():
        query = (SQL_DIR / sql_name).read_text(encoding="utf-8")
        result = pd.read_sql_query(query, conn)
        outputs[csv_name] = result
        result.to_csv(OUTPUT_DIR / csv_name, index=False)

    return outputs


def as_money(value: float) -> str:
    return f"GBP {value:,.0f}"


def as_pct(value: float) -> str:
    return f"{value:.1%}"


def generate_summary(outputs: dict[str, pd.DataFrame]) -> dict[str, object]:
    overview = outputs["dataset_overview.csv"].iloc[0].to_dict()
    customer_metrics = outputs["customer_metrics.csv"]
    rfm_summary = outputs["rfm_segment_summary.csv"]
    campaign_targets = outputs["campaign_targets.csv"]
    cohort = outputs["cohort_retention.csv"]
    monthly = outputs["monthly_kpis.csv"]

    top_segment = rfm_summary.sort_values("segment_revenue", ascending=False).iloc[0].to_dict()
    at_risk = rfm_summary[rfm_summary["rfm_segment"] == "At Risk High Value"]
    at_risk_row = at_risk.iloc[0].to_dict() if not at_risk.empty else {}

    repeat_rate = float(customer_metrics["repeat_customer_flag"].mean())
    latest_month = monthly.sort_values("transaction_month").iloc[-1].to_dict()
    first_three_months = cohort[cohort["months_since_first_purchase"].between(1, 3)]
    early_retention = (
        float(first_three_months["retention_rate"].mean())
        if not first_three_months.empty
        else 0.0
    )

    summary = {
        "analysis_date": overview["analysis_date"],
        "clean_rows": int(overview["clean_rows"]),
        "distinct_customers": int(overview["distinct_customers"]),
        "distinct_orders": int(overview["distinct_orders"]),
        "total_revenue": float(overview["total_revenue"]),
        "repeat_purchase_rate": repeat_rate,
        "top_segment": top_segment.get("rfm_segment", ""),
        "top_segment_revenue": float(top_segment.get("segment_revenue", 0.0)),
        "at_risk_high_value_customers": int(at_risk_row.get("customers", 0)),
        "at_risk_high_value_revenue": float(at_risk_row.get("segment_revenue", 0.0)),
        "campaign_target_count": int(len(campaign_targets)),
        "latest_month": latest_month["transaction_month"],
        "latest_month_revenue": float(latest_month["revenue"]),
        "average_month_1_to_3_retention": early_retention,
    }

    (OUTPUT_DIR / "portfolio_metrics.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    write_executive_summary(summary)
    return summary


def write_executive_summary(summary: dict[str, object]) -> None:
    md = f"""# Executive Summary

## Objective

Identify which existing customers should be prioritised for a retention campaign when marketing budget is limited.

## Dataset

- Analysis date: {summary["analysis_date"]}
- Clean transaction rows: {summary["clean_rows"]:,}
- Distinct customers: {summary["distinct_customers"]:,}
- Distinct orders: {summary["distinct_orders"]:,}
- Total clean revenue: {as_money(float(summary["total_revenue"]))}

## Key findings

- Repeat purchase rate across known customers is {as_pct(float(summary["repeat_purchase_rate"]))}.
- The highest revenue RFM segment is `{summary["top_segment"]}`, contributing {as_money(float(summary["top_segment_revenue"]))}.
- `{summary["at_risk_high_value_customers"]}` customers are classified as `At Risk High Value`, representing {as_money(float(summary["at_risk_high_value_revenue"]))} in historical revenue.
- The campaign target list contains `{summary["campaign_target_count"]}` customers prioritised by historical value, order frequency, and inactivity.
- Average month 1 to 3 cohort retention is {as_pct(float(summary["average_month_1_to_3_retention"]))}.

## Recommended CRM action

Prioritise the `At Risk High Value` segment first. These customers have meaningful historical spend but have not purchased recently, making them better candidates for a targeted retention campaign than low-value inactive customers.

## Measurement recommendation

Run an A/B test on the campaign target list. Randomly assign eligible customers into treatment and control groups, then compare repeat purchase rate, revenue per customer, and average order value over a fixed measurement window.
"""
    (OUTPUT_DIR / "executive_summary.md").write_text(md, encoding="utf-8")


def table_html(df: pd.DataFrame, max_rows: int = 10) -> str:
    subset = df.head(max_rows).copy()
    rows = []
    rows.append("<table>")
    rows.append("<thead><tr>")
    for col in subset.columns:
        rows.append(f"<th>{html.escape(str(col))}</th>")
    rows.append("</tr></thead><tbody>")
    for _, row in subset.iterrows():
        rows.append("<tr>")
        for value in row:
            rows.append(f"<td>{html.escape(str(value))}</td>")
        rows.append("</tr>")
    rows.append("</tbody></table>")
    return "\n".join(rows)


def generate_dashboard(outputs: dict[str, pd.DataFrame], summary: dict[str, object]) -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    rfm_summary = outputs["rfm_segment_summary.csv"].copy()
    campaign = outputs["campaign_targets.csv"].head(12).copy()
    cohort = outputs["cohort_retention.csv"].copy()
    monthly = outputs["monthly_kpis.csv"].tail(12).copy()

    max_segment_revenue = max(float(rfm_summary["segment_revenue"].max()), 1.0)
    segment_cards = []
    for _, row in rfm_summary.sort_values("segment_revenue", ascending=False).iterrows():
        width = 100 * float(row["segment_revenue"]) / max_segment_revenue
        segment_cards.append(
            f"""
            <div class="bar-row">
              <div class="bar-label">{html.escape(str(row["rfm_segment"]))}</div>
              <div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div>
              <div class="bar-value">{int(row["customers"]):,} customers | {as_money(float(row["segment_revenue"]))}</div>
            </div>
            """
        )

    cohort_pivot = cohort.pivot_table(
        index="cohort_month",
        columns="months_since_first_purchase",
        values="retention_rate",
        aggfunc="first",
    ).fillna(0)
    cohort_pivot = cohort_pivot.loc[:, [c for c in cohort_pivot.columns if int(c) <= 12]]
    heatmap_rows = ["<table class='heatmap'><thead><tr><th>Cohort</th>"]
    for col in cohort_pivot.columns:
        heatmap_rows.append(f"<th>M+{int(col)}</th>")
    heatmap_rows.append("</tr></thead><tbody>")
    for idx, row in cohort_pivot.tail(12).iterrows():
        heatmap_rows.append(f"<tr><th>{html.escape(str(idx))}</th>")
        for value in row:
            shade = int(245 - min(float(value), 1.0) * 160)
            heatmap_rows.append(
                f"<td style='background:rgb({shade},{shade + 8},255)'>{float(value):.1%}</td>"
            )
        heatmap_rows.append("</tr>")
    heatmap_rows.append("</tbody></table>")

    monthly_table = monthly[
        [
            "transaction_month",
            "revenue",
            "orders",
            "customers",
            "average_order_value",
            "repeat_purchase_rate",
        ]
    ].copy()
    monthly_table["revenue"] = monthly_table["revenue"].map(lambda x: as_money(float(x)))
    monthly_table["average_order_value"] = monthly_table["average_order_value"].map(
        lambda x: as_money(float(x))
    )
    monthly_table["repeat_purchase_rate"] = monthly_table["repeat_purchase_rate"].map(
        lambda x: as_pct(float(x))
    )

    campaign_table = campaign[
        [
            "priority_rank",
            "customer_id",
            "total_revenue",
            "total_orders",
            "days_since_last_purchase",
            "rfm_segment",
        ]
    ].copy()
    campaign_table["total_revenue"] = campaign_table["total_revenue"].map(
        lambda x: as_money(float(x))
    )

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Customer Retention Dashboard</title>
  <style>
    :root {{
      --ink: #17202a;
      --muted: #5b6675;
      --line: #d9dee7;
      --blue: #2f5fbb;
      --green: #24795b;
      --amber: #9d6420;
      --bg: #f7f8fb;
      --panel: #ffffff;
    }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: var(--bg);
    }}
    header {{
      padding: 28px 36px 18px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      letter-spacing: 0;
    }}
    h2 {{
      font-size: 18px;
      margin: 0 0 14px;
    }}
    p {{
      color: var(--muted);
      line-height: 1.5;
      margin: 0;
    }}
    main {{
      padding: 24px 36px 40px;
      display: grid;
      gap: 22px;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(160px, 1fr));
      gap: 14px;
    }}
    .kpi, section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    .kpi-title {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0;
      margin-bottom: 8px;
    }}
    .kpi-value {{
      font-size: 24px;
      font-weight: 700;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 22px;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: 150px 1fr 220px;
      align-items: center;
      gap: 12px;
      margin: 11px 0;
      font-size: 13px;
    }}
    .bar-track {{
      height: 12px;
      border-radius: 4px;
      background: #e9edf5;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      background: var(--blue);
    }}
    .bar-value {{
      color: var(--muted);
      text-align: right;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    th, td {{
      padding: 8px 9px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      white-space: nowrap;
    }}
    th {{
      color: var(--muted);
      font-weight: 700;
      background: #fbfcff;
    }}
    .heatmap td, .heatmap th {{
      text-align: center;
      padding: 7px;
    }}
    .note {{
      color: var(--muted);
      font-size: 13px;
      margin-top: 10px;
    }}
    @media (max-width: 900px) {{
      .kpi-grid, .grid-2 {{
        grid-template-columns: 1fr;
      }}
      .bar-row {{
        grid-template-columns: 1fr;
      }}
      .bar-value {{
        text-align: left;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Customer Retention Dashboard</h1>
    <p>SQL-driven retention, RFM segmentation, cohort analysis and campaign targeting for an online retail dataset.</p>
  </header>
  <main>
    <div class="kpi-grid">
      <div class="kpi"><div class="kpi-title">Total Revenue</div><div class="kpi-value">{as_money(float(summary["total_revenue"]))}</div></div>
      <div class="kpi"><div class="kpi-title">Customers</div><div class="kpi-value">{int(summary["distinct_customers"]):,}</div></div>
      <div class="kpi"><div class="kpi-title">Orders</div><div class="kpi-value">{int(summary["distinct_orders"]):,}</div></div>
      <div class="kpi"><div class="kpi-title">Repeat Purchase Rate</div><div class="kpi-value">{as_pct(float(summary["repeat_purchase_rate"]))}</div></div>
    </div>

    <section>
      <h2>RFM Segment Revenue</h2>
      {''.join(segment_cards)}
      <div class="note">Revenue bars use historical clean transaction revenue by customer segment.</div>
    </section>

    <div class="grid-2">
      <section>
        <h2>Recent Monthly KPIs</h2>
        {table_html(monthly_table, max_rows=12)}
      </section>
      <section>
        <h2>Top Campaign Targets</h2>
        {table_html(campaign_table, max_rows=12)}
        <div class="note">Targets prioritise high-value inactive customers for CRM testing.</div>
      </section>
    </div>

    <section>
      <h2>Cohort Retention Heatmap</h2>
      {''.join(heatmap_rows)}
      <div class="note">M+0 is the first purchase month. Later columns show the share of the original cohort that purchased again in each later month.</div>
    </section>

    <section>
      <h2>Business Recommendation</h2>
      <p>Prioritise At Risk High Value customers first, then test campaign impact through a treatment/control split. Track repeat purchase rate, revenue per customer and average order value during the measurement window.</p>
    </section>
  </main>
</body>
</html>
"""
    (DASHBOARD_DIR / "customer_retention_dashboard.html").write_text(
        html_doc, encoding="utf-8"
    )


def main() -> None:
    input_path = DEFAULT_INPUT
    df = load_transactions(input_path)
    with create_database(df) as conn:
        outputs = run_sql_outputs(conn)
    summary = generate_summary(outputs)
    generate_dashboard(outputs, summary)

    print("Generated project outputs:")
    for csv_name in QUERY_OUTPUTS.values():
        print(f"- {OUTPUT_DIR / csv_name}")
    print(f"- {OUTPUT_DIR / 'executive_summary.md'}")
    print(f"- {DASHBOARD_DIR / 'customer_retention_dashboard.html'}")


if __name__ == "__main__":
    main()
