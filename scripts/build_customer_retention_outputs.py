from __future__ import annotations

import html
import json
import math
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
FIGURES_DIR = PROJECT_ROOT / "documentation" / "figures"


QUERY_OUTPUTS = {
    "00_dataset_overview.sql": "dataset_overview.csv",
    "01_customer_kpis.sql": "customer_metrics.csv",
    "02_rfm_segmentation.sql": "rfm_segments.csv",
    "02b_rfm_segment_summary.sql": "rfm_segment_summary.csv",
    "03_cohort_retention.sql": "cohort_retention.csv",
    "04_campaign_targets.sql": "campaign_targets.csv",
    "05_monthly_kpis.sql": "monthly_kpis.csv",
    "06_repeat_customer_summary.sql": "repeat_customer_summary.csv",
    "07_data_quality_checks.sql": "data_quality_checks.csv",
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


def generate_monthly_forecast(outputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    monthly = outputs["monthly_kpis.csv"].sort_values("transaction_month").reset_index(drop=True)
    forecast_rows: list[dict[str, object]] = []
    window = 3
    horizon = 3

    metric_specs = [
        ("monthly_revenue", "revenue", "GBP", None),
        ("monthly_repeat_purchase_rate", "repeat_purchase_rate", "share", 1.0),
    ]

    for metric_name, source_column, unit, upper_cap in metric_specs:
        values = monthly[source_column].astype(float).reset_index(drop=True)
        months = pd.to_datetime(monthly["transaction_month"]).reset_index(drop=True)
        backtest_errors: list[float] = []
        backtest_pct_errors: list[float] = []

        for index in range(window, len(values)):
            prediction = float(values.iloc[index - window:index].mean())
            actual = float(values.iloc[index])
            error = actual - prediction
            backtest_errors.append(abs(error))
            if actual != 0:
                backtest_pct_errors.append(abs(error) / abs(actual))

        mae = float(sum(backtest_errors) / len(backtest_errors)) if backtest_errors else 0.0
        mape = (
            float(sum(backtest_pct_errors) / len(backtest_pct_errors))
            if backtest_pct_errors
            else 0.0
        )

        rolling_values = values.iloc[-window:].astype(float).tolist()
        last_month = months.iloc[-1]

        for step in range(1, horizon + 1):
            forecast_value = float(sum(rolling_values[-window:]) / window)
            lower_value = max(0.0, forecast_value - mae)
            upper_value = forecast_value + mae
            if upper_cap is not None:
                upper_value = min(upper_cap, upper_value)

            forecast_rows.append(
                {
                    "metric": metric_name,
                    "forecast_month": (last_month + pd.DateOffset(months=step)).strftime(
                        "%Y-%m-01"
                    ),
                    "method": "3-month moving average baseline",
                    "forecast_value": round(forecast_value, 4),
                    "lower_practical_band": round(lower_value, 4),
                    "upper_practical_band": round(upper_value, 4),
                    "validation_mae": round(mae, 4),
                    "validation_mape": round(mape, 4),
                    "validation_periods": len(backtest_errors),
                    "unit": unit,
                    "note": "Transparent baseline for short-term planning, not a production forecast.",
                }
            )
            rolling_values.append(forecast_value)

    forecast = pd.DataFrame(forecast_rows)
    forecast.to_csv(OUTPUT_DIR / "monthly_forecast.csv", index=False)
    return forecast


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
    quality = outputs["data_quality_checks.csv"]
    forecast = outputs["monthly_forecast.csv"]

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
    quality_passed = int((quality["status"] == "Pass").sum())
    quality_total = int(len(quality))
    quality_review = int((quality["status"] != "Pass").sum())
    next_revenue_forecast = forecast[
        (forecast["metric"] == "monthly_revenue") & (forecast["forecast_month"] > latest_month["transaction_month"])
    ].iloc[0]
    next_repeat_forecast = forecast[
        (forecast["metric"] == "monthly_repeat_purchase_rate")
        & (forecast["forecast_month"] > latest_month["transaction_month"])
    ].iloc[0]

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
        "data_quality_checks_passed": quality_passed,
        "data_quality_checks_total": quality_total,
        "data_quality_review_items": quality_review,
        "next_forecast_month": next_revenue_forecast["forecast_month"],
        "next_month_revenue_forecast": float(next_revenue_forecast["forecast_value"]),
        "next_month_repeat_purchase_rate_forecast": float(
            next_repeat_forecast["forecast_value"]
        ),
        "forecast_method": next_revenue_forecast["method"],
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
- Data quality checks passed: {summary["data_quality_checks_passed"]}/{summary["data_quality_checks_total"]}.
- Next-month revenue baseline forecast: {as_money(float(summary["next_month_revenue_forecast"]))} for {summary["next_forecast_month"]}.

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
"""
    (OUTPUT_DIR / "executive_summary.md").write_text(md, encoding="utf-8")


def write_svg(path: Path, title: str, description: str, width: int, height: int, body: str) -> None:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="chart-title chart-description">
  <title id="chart-title">{html.escape(title)}</title>
  <desc id="chart-description">{html.escape(description)}</desc>
  <rect width="100%" height="100%" fill="#ffffff"/>
  <g font-family="Arial, Helvetica, sans-serif">{body}</g>
</svg>
'''
    path.write_text(svg, encoding="utf-8")


def chart_text(value: object, x: float, y: float, size: int = 14, anchor: str = "start", weight: str = "400", fill: str = "#17202a") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}px" text-anchor="{anchor}" '
        f'font-weight="{weight}" fill="{fill}">{html.escape(str(value))}</text>'
    )


def generate_figures(outputs: dict[str, pd.DataFrame], summary: dict[str, object]) -> None:
    """Create static, dependency-light SVG charts from the same SQL outputs as the dashboard."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Segment revenue chart.
    rfm = outputs["rfm_segment_summary.csv"].sort_values("segment_revenue").reset_index(drop=True)
    width, height = 1100, 620
    left, right, top, bottom = 285, 210, 105, 70
    plot_width = width - left - right
    max_value = max(float(rfm["segment_revenue"].max()), 1.0)
    row_height, gap = 42, 18
    body = [chart_text("Historical value is concentrated in Champions; At Risk High Value is the retention opportunity", 40, 48, 17, weight="500")]
    for tick in range(0, 5):
        tick_value = max_value * tick / 4
        x = left + plot_width * tick / 4
        body.append(f'<line x1="{x:.1f}" y1="{top - 15}" x2="{x:.1f}" y2="{height - bottom}" stroke="#d9dee7" stroke-width="1"/>')
        body.append(chart_text(f"GBP {tick_value / 1_000_000:.1f}m", x, height - 30, 11, anchor="middle", fill="#5b6675"))
    for index, row in rfm.iterrows():
        y = top + index * (row_height + gap)
        value = float(row["segment_revenue"])
        bar_width = plot_width * value / max_value
        color = "#c2410c" if row["rfm_segment"] == "At Risk High Value" else "#94a3b8"
        body.append(chart_text(row["rfm_segment"], left - 15, y + 27, 13, anchor="end"))
        body.append(f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="{row_height}" rx="4" fill="{color}"/>')
        body.append(chart_text(f"GBP {value / 1_000_000:.2f}m", min(left + bar_width + 12, width - 8), y + 27, 12, fill="#334155"))
    write_svg(
        FIGURES_DIR / "segment_revenue.svg",
        "Historical revenue by RFM segment",
        "Horizontal bars compare historical revenue across RFM customer segments and highlight the At Risk High Value segment.",
        width,
        height,
        "".join(body),
    )

    def line_panel(values: list[float], labels: list[str], x0: int, y0: int, panel_width: int, panel_height: int, title: str, color: str, value_formatter) -> list[str]:
        panel = [chart_text(title, x0, y0, 16, weight="500")]
        plot_top = y0 + 28
        plot_bottom = y0 + panel_height - 30
        maximum = max(max(values), 1.0) * 1.12
        for fraction in (0, 0.5, 1):
            y = plot_bottom - (plot_bottom - plot_top) * fraction
            panel.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + panel_width}" y2="{y:.1f}" stroke="#d9dee7" stroke-width="1"/>')
            panel.append(chart_text(value_formatter(maximum * fraction), x0 - 10, y + 4, 11, anchor="end", fill="#5b6675"))
        points = []
        for index, value in enumerate(values):
            x = x0 + panel_width * index / max(len(values) - 1, 1)
            y = plot_bottom - (plot_bottom - plot_top) * value / maximum
            points.append((x, y))
        point_string = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        panel.append(f'<polyline points="{point_string}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
        for x, y in points:
            panel.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#ffffff" stroke="{color}" stroke-width="2"/>')
        for index, label in enumerate(labels):
            if index % max(1, math.ceil(len(labels) / 7)) == 0 or index == len(labels) - 1:
                x = x0 + panel_width * index / max(len(labels) - 1, 1)
                panel.append(chart_text(label, x, plot_bottom + 22, 10, anchor="middle", fill="#5b6675"))
        return panel

    monthly = outputs["monthly_kpis.csv"].copy()
    monthly_labels = pd.to_datetime(monthly["transaction_month"]).dt.strftime("%Y-%m").tolist()
    monthly_body = [chart_text("Monthly revenue is volatile, so targeting should use customer-level value", 80, 42, 19, weight="500")]
    monthly_body += line_panel(
        monthly["revenue"].astype(float).tolist(),
        monthly_labels,
        105,
        82,
        900,
        250,
        "Monthly revenue",
        "#2563eb",
        lambda value: f"GBP {value / 1_000_000:.1f}m",
    )
    monthly_body += line_panel(
        (monthly["repeat_purchase_rate"].astype(float) * 100).tolist(),
        monthly_labels,
        105,
        375,
        900,
        250,
        "Monthly repeat-purchase rate",
        "#0f766e",
        lambda value: f"{value:.0f}%",
    )
    write_svg(
        FIGURES_DIR / "monthly_kpis.svg",
        "Monthly revenue and repeat-purchase KPIs",
        "Two line charts show monthly revenue and the monthly share of customers placing at least two orders.",
        1100,
        670,
        "".join(monthly_body),
    )

    # Revenue forecast baseline.
    forecast = outputs.get("monthly_forecast.csv")
    if forecast is not None and not forecast.empty:
        revenue_forecast = forecast[forecast["metric"] == "monthly_revenue"].copy()
        historical = monthly.tail(12).copy()
        historical["transaction_month"] = pd.to_datetime(historical["transaction_month"])
        revenue_forecast["forecast_month"] = pd.to_datetime(revenue_forecast["forecast_month"])

        width, height = 1100, 530
        left, right, top, bottom = 105, 90, 85, 85
        plot_width = width - left - right
        plot_height = height - top - bottom
        historical_values = historical["revenue"].astype(float).tolist()
        forecast_values = revenue_forecast["forecast_value"].astype(float).tolist()
        upper_values = revenue_forecast["upper_practical_band"].astype(float).tolist()
        maximum = max(historical_values + forecast_values + upper_values) * 1.12
        all_labels = (
            historical["transaction_month"].dt.strftime("%Y-%m").tolist()
            + revenue_forecast["forecast_month"].dt.strftime("%Y-%m").tolist()
        )
        total_points = len(all_labels)

        def point_x(index: int) -> float:
            return left + plot_width * index / max(total_points - 1, 1)

        def point_y(value: float) -> float:
            return top + plot_height - plot_height * value / maximum

        body = [
            chart_text(
                "Short-term revenue forecast baseline from recent monthly performance",
                left,
                45,
                19,
                weight="500",
            )
        ]
        for fraction in (0, 0.25, 0.5, 0.75, 1):
            y = top + plot_height - plot_height * fraction
            body.append(
                f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="#d9dee7" stroke-width="1"/>'
            )
            body.append(
                chart_text(
                    f"GBP {maximum * fraction / 1_000_000:.1f}m",
                    left - 10,
                    y + 4,
                    11,
                    anchor="end",
                    fill="#5b6675",
                )
            )

        split_index = len(historical_values) - 1
        split_x = point_x(split_index) + (point_x(split_index + 1) - point_x(split_index)) / 2
        body.append(
            f'<line x1="{split_x:.1f}" y1="{top}" x2="{split_x:.1f}" y2="{top + plot_height}" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5 5"/>'
        )
        body.append(chart_text("Forecast", split_x + 12, top + 18, 12, fill="#5b6675"))

        historical_points = [
            (point_x(index), point_y(value)) for index, value in enumerate(historical_values)
        ]
        body.append(
            '<polyline points="'
            + " ".join(f"{x:.1f},{y:.1f}" for x, y in historical_points)
            + '" fill="none" stroke="#2563eb" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        )

        forecast_points = [
            (point_x(split_index), point_y(historical_values[-1])),
            *[
                (point_x(split_index + step), point_y(value))
                for step, value in enumerate(forecast_values, 1)
            ],
        ]
        body.append(
            '<polyline points="'
            + " ".join(f"{x:.1f},{y:.1f}" for x, y in forecast_points)
            + '" fill="none" stroke="#c2410c" stroke-width="3" stroke-dasharray="8 6" stroke-linejoin="round" stroke-linecap="round"/>'
        )

        for step, row in enumerate(revenue_forecast.itertuples(index=False), 1):
            x = point_x(split_index + step)
            y_low = point_y(float(row.lower_practical_band))
            y_high = point_y(float(row.upper_practical_band))
            y_mid = point_y(float(row.forecast_value))
            body.append(
                f'<line x1="{x:.1f}" y1="{y_low:.1f}" x2="{x:.1f}" y2="{y_high:.1f}" stroke="#c2410c" stroke-width="2" opacity="0.65"/>'
            )
            body.append(f'<circle cx="{x:.1f}" cy="{y_mid:.1f}" r="5" fill="#ffffff" stroke="#c2410c" stroke-width="2"/>')

        for index, label in enumerate(all_labels):
            if index % 2 == 0 or index >= split_index:
                body.append(
                    chart_text(
                        label,
                        point_x(index),
                        top + plot_height + 28,
                        10,
                        anchor="middle",
                        fill="#5b6675",
                    )
                )

        body.append(chart_text("Historical", left + 4, height - 22, 12, fill="#2563eb"))
        body.append(chart_text("3-month moving average baseline", left + 110, height - 22, 12, fill="#c2410c"))
        write_svg(
            FIGURES_DIR / "monthly_forecast.svg",
            "Monthly revenue forecast baseline",
            "Line chart showing recent historical revenue, a three-month moving average forecast and practical uncertainty bands.",
            width,
            height,
            "".join(body),
        )

    # Cohort retention heatmap.
    cohort = outputs["cohort_retention.csv"].copy()
    cohort_pivot = cohort.pivot_table(
        index="cohort_month",
        columns="months_since_first_purchase",
        values="retention_rate",
        aggfunc="first",
    )
    visible_columns = [column for column in cohort_pivot.columns if int(column) <= 12]
    cohort_pivot = cohort_pivot.loc[:, visible_columns].tail(12)
    width, height = 1100, 610
    left, top, cell_width, cell_height = 145, 105, 68, 31
    body = [chart_text("Retention drops sharply after the first purchase month", left, 45, 19, weight="500")]
    body.append(chart_text("Months since first purchase", left + 6 * cell_width, 585, 13, anchor="middle", fill="#5b6675"))
    for column_index, column in enumerate(cohort_pivot.columns):
        x = left + column_index * cell_width
        body.append(chart_text(f"M+{int(column)}", x + cell_width / 2, 88, 11, anchor="middle", fill="#5b6675"))
    for row_index, (cohort_name, row) in enumerate(cohort_pivot.iterrows()):
        y = top + row_index * cell_height
        body.append(chart_text(cohort_name, left - 12, y + 21, 11, anchor="end", fill="#5b6675"))
        for column_index, value in enumerate(row):
            x = left + column_index * cell_width
            if pd.isna(value):
                fill = "#f1f5f9"
                label = ""
            else:
                strength = min(max(float(value), 0.0), 1.0)
                red = int(224 - 195 * strength)
                green = int(242 - 177 * strength)
                blue = int(254 - 34 * strength)
                fill = f"rgb({red},{green},{blue})"
                label = f"{float(value):.0%}"
            body.append(f'<rect x="{x}" y="{y}" width="{cell_width - 2}" height="{cell_height - 2}" rx="2" fill="{fill}"/>')
            if label:
                text_color = "#ffffff" if float(value) >= 0.55 else "#17202a"
                body.append(chart_text(label, x + (cell_width - 2) / 2, y + 20, 10, anchor="middle", fill=text_color))
    write_svg(
        FIGURES_DIR / "cohort_retention.svg",
        "Cohort retention heatmap",
        "Heatmap showing the percentage of each acquisition cohort that purchased again in later months.",
        width,
        height,
        "".join(body),
    )

    # Campaign decision funnel.
    values = [
        int(summary["distinct_customers"]),
        int(summary["at_risk_high_value_customers"]),
        int(summary["campaign_target_count"]),
    ]
    labels = ["All known\ncustomers", "At-risk high-value\ncustomers", "Prioritised target\nlist"]
    width, height = 950, 570
    left, right, top, bottom = 90, 70, 100, 90
    plot_width, plot_height = width - left - right, height - top - bottom
    max_value = max(values)
    body = [chart_text("The campaign decision narrows the customer base to 300 testable targets", left, 48, 19, weight="500")]
    for tick in range(0, 5):
        value = max_value * tick / 4
        y = top + plot_height - plot_height * tick / 4
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="#d9dee7" stroke-width="1"/>')
        body.append(chart_text(f"{value / 1_000:.0f}k" if value >= 1000 else f"{value:.0f}", left - 10, y + 4, 11, anchor="end", fill="#5b6675"))
    bar_width = 150
    colors = ["#94a3b8", "#c2410c", "#2563eb"]
    for index, (value, label) in enumerate(zip(values, labels)):
        x = left + (index + 0.5) * plot_width / 3 - bar_width / 2
        bar_height = plot_height * value / max_value
        y = top + plot_height - bar_height
        body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" rx="4" fill="{colors[index]}"/>')
        body.append(chart_text(f"{value:,}", x + bar_width / 2, y - 10, 14, anchor="middle", weight="500"))
        label_lines = label.split("\n")
        for line_index, line in enumerate(label_lines):
            body.append(chart_text(line, x + bar_width / 2, height - bottom + 25 + line_index * 17, 12, anchor="middle", fill="#334155"))
    write_svg(
        FIGURES_DIR / "campaign_funnel.svg",
        "Campaign decision funnel",
        "Bars show the reduction from all known customers to the high-value inactive segment and the prioritised campaign list.",
        width,
        height,
        "".join(body),
    )


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
    .figure-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 22px;
    }}
    figure {{
      margin: 0;
    }}
    figure img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    @media (max-width: 900px) {{
      .kpi-grid, .grid-2, .figure-grid {{
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

    <div class="figure-grid">
      <section>
        <h2>Decision evidence: segment revenue</h2>
        <figure><img src="../documentation/figures/segment_revenue.svg" alt="Historical revenue by RFM segment"></figure>
      </section>
      <section>
        <h2>Decision evidence: campaign scope</h2>
        <figure><img src="../documentation/figures/campaign_funnel.svg" alt="Campaign decision funnel"></figure>
      </section>
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
    outputs["monthly_forecast.csv"] = generate_monthly_forecast(outputs)
    summary = generate_summary(outputs)
    generate_figures(outputs, summary)
    generate_dashboard(outputs, summary)

    print("Generated project outputs:")
    for csv_name in QUERY_OUTPUTS.values():
        print(f"- {OUTPUT_DIR / csv_name}")
    print(f"- {OUTPUT_DIR / 'monthly_forecast.csv'}")
    print(f"- {OUTPUT_DIR / 'executive_summary.md'}")
    for figure_name in (
        "segment_revenue.svg",
        "monthly_kpis.svg",
        "monthly_forecast.svg",
        "cohort_retention.svg",
        "campaign_funnel.svg",
    ):
        print(f"- {FIGURES_DIR / figure_name}")
    print(f"- {DASHBOARD_DIR / 'customer_retention_dashboard.html'}")


if __name__ == "__main__":
    main()
