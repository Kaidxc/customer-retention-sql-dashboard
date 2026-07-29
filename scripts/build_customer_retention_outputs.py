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
    "02_order_purchase_summary.sql": "order_purchase_summary.csv",
    "05_monthly_kpis.sql": "monthly_kpis.csv",
    "06_repeat_customer_summary.sql": "repeat_customer_summary.csv",
    "07_data_quality_checks.sql": "data_quality_checks.csv",
    "08_product_performance.sql": "product_performance.csv",
    "09_product_revenue_concentration.sql": "product_revenue_concentration.csv",
    "10_product_quarterly_sales.sql": "product_quarterly_sales.csv",
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


def generate_customer_profile_summary(outputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    customer_metrics = outputs["customer_metrics.csv"].copy()
    total_customers = len(customer_metrics)
    rows: list[dict[str, object]] = []

    def add_bucket_summary(
        feature: str,
        values: pd.Series,
        bins: list[float],
        labels: list[str],
        description: str,
    ) -> None:
        bucketed = pd.cut(values, bins=bins, labels=labels, include_lowest=True)
        counts = bucketed.value_counts(sort=False)
        for label, count in counts.items():
            rows.append(
                {
                    "feature": feature,
                    "bucket": str(label),
                    "customers": int(count),
                    "customer_share": round(count / total_customers, 4),
                    "description": description,
                }
            )

    repeat_counts = customer_metrics["repeat_customer_flag"].map(
        {0: "One-time customer", 1: "Repeat customer"}
    ).value_counts(sort=False)
    for label in ("One-time customer", "Repeat customer"):
        count = int(repeat_counts.get(label, 0))
        rows.append(
            {
                "feature": "repeat_status",
                "bucket": label,
                "customers": count,
                "customer_share": round(count / total_customers, 4),
                "description": "Whether a customer placed one order or at least two orders.",
            }
        )

    add_bucket_summary(
        "total_orders",
        customer_metrics["total_orders"],
        [0, 1, 2, 5, 10, 20, float("inf")],
        ["1", "2", "3-5", "6-10", "11-20", "21+"],
        "Distinct completed orders per customer.",
    )
    add_bucket_summary(
        "total_revenue",
        customer_metrics["total_revenue"],
        [-0.01, 100, 500, 1000, 5000, float("inf")],
        ["<=GBP100", "GBP100-500", "GBP500-1k", "GBP1k-5k", "GBP5k+"],
        "Historical revenue per customer.",
    )
    add_bucket_summary(
        "days_since_last_purchase",
        customer_metrics["days_since_last_purchase"],
        [-1, 30, 90, 180, 365, float("inf")],
        ["0-30 days", "31-90 days", "91-180 days", "181-365 days", "365+ days"],
        "Inactivity measured from the analysis date to the customer's last purchase.",
    )
    add_bucket_summary(
        "average_order_value",
        customer_metrics["average_order_value"],
        [-0.01, 25, 50, 100, 250, float("inf")],
        ["<=GBP25", "GBP25-50", "GBP50-100", "GBP100-250", "GBP250+"],
        "Average order value per customer.",
    )

    profile = pd.DataFrame(rows)
    profile.to_csv(OUTPUT_DIR / "customer_profile_summary.csv", index=False)
    return profile


def generate_purchase_behavior_summary(outputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    orders = outputs["order_purchase_summary.csv"].copy()
    total_orders = len(orders)
    rows: list[dict[str, object]] = []

    def add_bucket_summary(
        feature: str,
        values: pd.Series,
        bins: list[float],
        labels: list[str],
        description: str,
    ) -> None:
        bucketed = pd.cut(values, bins=bins, labels=labels, include_lowest=True)
        counts = bucketed.value_counts(sort=False)
        for label, count in counts.items():
            rows.append(
                {
                    "feature": feature,
                    "bucket": str(label),
                    "orders": int(count),
                    "order_share": round(count / total_orders, 4),
                    "description": description,
                }
            )

    add_bucket_summary(
        "order_value",
        orders["order_value"],
        [-0.01, 25, 50, 100, 250, 500, float("inf")],
        ["<=GBP25", "GBP25-50", "GBP50-100", "GBP100-250", "GBP250-500", "GBP500+"],
        "Total value of a completed invoice.",
    )
    add_bucket_summary(
        "units_purchased",
        orders["units_purchased"],
        [0, 5, 10, 25, 50, 100, float("inf")],
        ["1-5", "6-10", "11-25", "26-50", "51-100", "101+"],
        "Total units purchased in a completed invoice.",
    )
    add_bucket_summary(
        "distinct_products",
        orders["distinct_products"],
        [0, 1, 3, 6, 10, 20, float("inf")],
        ["1", "2-3", "4-6", "7-10", "11-20", "21+"],
        "Distinct stock codes included in a completed invoice.",
    )

    summary = pd.DataFrame(rows)
    summary.to_csv(OUTPUT_DIR / "purchase_behavior_summary.csv", index=False)
    return summary


def generate_product_report_outputs(outputs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    product_performance = outputs["product_performance.csv"].copy()
    merchandise = product_performance[
        product_performance["stock_line_type"] == "merchandise"
    ].copy()
    merchandise["last_sale_date"] = pd.to_datetime(merchandise["last_sale_date"])
    analysis_date = pd.to_datetime(outputs["dataset_overview.csv"].iloc[0]["analysis_date"])
    merchandise["days_since_last_sale"] = (
        analysis_date - merchandise["last_sale_date"]
    ).dt.days

    top_quantity = merchandise.sort_values("total_quantity", ascending=False).head(10)
    top_revenue = merchandise.sort_values("total_revenue", ascending=False).head(10)
    top_quantity.to_csv(OUTPUT_DIR / "top_products_by_quantity.csv", index=False)
    top_revenue.to_csv(OUTPUT_DIR / "top_products_by_revenue.csv", index=False)

    slow_moving = merchandise[
        (merchandise["total_revenue"] >= 5000)
        & (merchandise["days_since_last_sale"] >= 180)
    ].sort_values("total_revenue", ascending=False).head(25)
    slow_moving.to_csv(OUTPUT_DIR / "slow_moving_product_candidates.csv", index=False)

    summary_rows: list[dict[str, object]] = []

    def add_bucket_summary(
        feature: str,
        values: pd.Series,
        bins: list[float],
        labels: list[str],
        description: str,
    ) -> None:
        bucketed = pd.cut(values, bins=bins, labels=labels, include_lowest=True)
        counts = bucketed.value_counts(sort=False)
        total = int(counts.sum())
        for label, count in counts.items():
            summary_rows.append(
                {
                    "feature": feature,
                    "bucket": str(label),
                    "products": int(count),
                    "product_share": round(int(count) / max(total, 1), 4),
                    "description": description,
                }
            )

    add_bucket_summary(
        "active_months",
        merchandise["active_months"],
        [0, 1, 3, 6, 12, 18, 25],
        ["1", "2-3", "4-6", "7-12", "13-18", "19-25"],
        "Number of months in which a merchandise product recorded sales.",
    )
    add_bucket_summary(
        "total_revenue",
        merchandise["total_revenue"],
        [-0.01, 100, 500, 1000, 5000, 10000, 50000, float("inf")],
        ["<=GBP100", "GBP100-500", "GBP500-1k", "GBP1k-5k", "GBP5k-10k", "GBP10k-50k", "GBP50k+"],
        "Historical revenue generated by a merchandise product.",
    )
    add_bucket_summary(
        "days_since_last_sale",
        merchandise["days_since_last_sale"],
        [-1, 30, 90, 180, 365, float("inf")],
        ["0-30 days", "31-90 days", "91-180 days", "181-365 days", "365+ days"],
        "Days since the product last appeared in a sale.",
    )

    product_catalog_summary = pd.DataFrame(summary_rows)
    product_catalog_summary.to_csv(OUTPUT_DIR / "product_catalog_summary.csv", index=False)

    return {
        "top_products_by_quantity.csv": top_quantity,
        "top_products_by_revenue.csv": top_revenue,
        "slow_moving_product_candidates.csv": slow_moving,
        "product_catalog_summary.csv": product_catalog_summary,
    }


def generate_product_quarterly_forecast(outputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    quarterly = outputs["product_quarterly_sales.csv"].copy()
    performance = outputs["product_performance.csv"].copy()
    merchandise = performance[
        (performance["stock_line_type"] == "merchandise")
        & (performance["active_months"] >= 18)
        & (performance["total_revenue"] >= 10000)
    ].sort_values("total_revenue", ascending=False).head(20)

    quarter_periods = pd.PeriodIndex(
        [str(q).replace("-Q", "Q") for q in quarterly["sale_quarter"].unique()],
        freq="Q",
    ).sort_values()
    latest_quarter = quarter_periods.max()
    next_quarter = latest_quarter + 1
    last_four_quarters = list(quarter_periods[-4:])

    rows: list[dict[str, object]] = []
    for product in merchandise.itertuples(index=False):
        product_rows = quarterly[quarterly["stock_code"] == product.stock_code].copy()
        product_rows["period"] = pd.PeriodIndex(
            [str(q).replace("-Q", "Q") for q in product_rows["sale_quarter"]],
            freq="Q",
        )
        product_rows = product_rows.set_index("period")
        aligned = product_rows.reindex(last_four_quarters).fillna(
            {
                "quantity_sold": 0,
                "revenue": 0,
                "order_count": 0,
                "customer_count": 0,
            }
        )
        forecast_quantity = float(aligned["quantity_sold"].astype(float).mean())
        forecast_revenue = float(aligned["revenue"].astype(float).mean())
        latest_row = aligned.iloc[-1]

        rows.append(
            {
                "stock_code": product.stock_code,
                "product_description": product.product_description,
                "next_quarter": f"{next_quarter.year}-Q{next_quarter.quarter}",
                "method": "Average of the last four quarters",
                "active_months": int(product.active_months),
                "historical_revenue": round(float(product.total_revenue), 2),
                "latest_quarter_quantity": int(latest_row["quantity_sold"]),
                "latest_quarter_revenue": round(float(latest_row["revenue"]), 2),
                "forecast_quantity": round(forecast_quantity, 0),
                "forecast_revenue": round(forecast_revenue, 2),
                "note": "Forecast limited to stable high-revenue merchandise products.",
            }
        )

    forecast = pd.DataFrame(rows)
    forecast.to_csv(OUTPUT_DIR / "product_next_quarter_forecast.csv", index=False)
    return forecast


def as_money(value: float) -> str:
    return f"GBP {value:,.0f}"


def as_pct(value: float) -> str:
    return f"{value:.1%}"


def generate_summary(outputs: dict[str, pd.DataFrame]) -> dict[str, object]:
    overview = outputs["dataset_overview.csv"].iloc[0].to_dict()
    customer_metrics = outputs["customer_metrics.csv"]
    customer_profile = outputs["customer_profile_summary.csv"]
    order_summary = outputs["order_purchase_summary.csv"]
    quality = outputs["data_quality_checks.csv"]
    product_performance = outputs["product_performance.csv"]
    product_concentration = outputs["product_revenue_concentration.csv"]
    top_quantity = outputs["top_products_by_quantity.csv"]
    top_revenue = outputs["top_products_by_revenue.csv"]
    slow_products = outputs["slow_moving_product_candidates.csv"]
    product_forecast = outputs["product_next_quarter_forecast.csv"]

    quality_passed = int((quality["status"] == "Pass").sum())
    quality_total = int(len(quality))
    quality_review = int((quality["status"] != "Pass").sum())
    merchandise = product_performance[
        product_performance["stock_line_type"] == "merchandise"
    ]
    service_or_admin = product_performance[
        product_performance["stock_line_type"] == "service_or_admin_line"
    ]
    top_10_revenue_share = float(
        product_concentration[product_concentration["product_group"] == "Top 10"][
            "revenue_share"
        ].iloc[0]
    )
    top_100_revenue_share = float(
        product_concentration[product_concentration["product_group"] == "Top 100"][
            "revenue_share"
        ].iloc[0]
    )
    top_500_revenue_share = float(
        product_concentration[product_concentration["product_group"] == "Top 500"][
            "revenue_share"
        ].iloc[0]
    )
    top_quantity_product = top_quantity.iloc[0].to_dict()
    top_revenue_product = top_revenue.iloc[0].to_dict()
    broad_demand_product = (
        merchandise.sort_values(["customer_count", "order_count"], ascending=False)
        .iloc[0]
        .to_dict()
    )
    forecast_total_revenue = float(product_forecast["forecast_revenue"].sum())
    forecast_total_quantity = float(product_forecast["forecast_quantity"].sum())
    one_time_customers = int(
        customer_profile[
            (customer_profile["feature"] == "repeat_status")
            & (customer_profile["bucket"] == "One-time customer")
        ]["customers"].iloc[0]
    )
    repeat_customers = int(
        customer_profile[
            (customer_profile["feature"] == "repeat_status")
            & (customer_profile["bucket"] == "Repeat customer")
        ]["customers"].iloc[0]
    )

    summary = {
        "analysis_date": overview["analysis_date"],
        "clean_rows": int(overview["clean_rows"]),
        "distinct_customers": int(overview["distinct_customers"]),
        "distinct_orders": int(overview["distinct_orders"]),
        "total_revenue": float(overview["total_revenue"]),
        "data_quality_checks_passed": quality_passed,
        "data_quality_checks_total": quality_total,
        "data_quality_review_items": quality_review,
        "stock_codes": int(len(product_performance)),
        "merchandise_products": int(len(merchandise)),
        "service_or_admin_lines": int(len(service_or_admin)),
        "product_descriptions": int(product_performance["product_description"].nunique()),
        "top_10_revenue_share": top_10_revenue_share,
        "top_100_revenue_share": top_100_revenue_share,
        "top_500_revenue_share": top_500_revenue_share,
        "top_quantity_product_code": top_quantity_product["stock_code"],
        "top_quantity_product_description": top_quantity_product["product_description"],
        "top_quantity_product_units": int(top_quantity_product["total_quantity"]),
        "top_quantity_product_revenue": float(top_quantity_product["total_revenue"]),
        "top_revenue_product_code": top_revenue_product["stock_code"],
        "top_revenue_product_description": top_revenue_product["product_description"],
        "top_revenue_product_units": int(top_revenue_product["total_quantity"]),
        "top_revenue_product_revenue": float(top_revenue_product["total_revenue"]),
        "broad_demand_product_code": broad_demand_product["stock_code"],
        "broad_demand_product_description": broad_demand_product["product_description"],
        "broad_demand_product_orders": int(broad_demand_product["order_count"]),
        "broad_demand_product_customers": int(broad_demand_product["customer_count"]),
        "broad_demand_product_revenue": float(broad_demand_product["total_revenue"]),
        "one_time_customers": one_time_customers,
        "repeat_customers": repeat_customers,
        "repeat_customer_share": repeat_customers / max(int(overview["distinct_customers"]), 1),
        "median_customer_orders": float(customer_metrics["total_orders"].median()),
        "median_customer_revenue": float(customer_metrics["total_revenue"].median()),
        "median_order_value": float(order_summary["order_value"].median()),
        "median_units_per_order": float(order_summary["units_purchased"].median()),
        "median_distinct_products_per_order": float(
            order_summary["distinct_products"].median()
        ),
        "slow_moving_candidate_count": int(len(slow_products)),
        "forecast_product_count": int(len(product_forecast)),
        "next_product_forecast_quarter": product_forecast["next_quarter"].iloc[0],
        "forecast_top_product_revenue": forecast_total_revenue,
        "forecast_top_product_quantity": forecast_total_quantity,
    }

    (OUTPUT_DIR / "portfolio_metrics.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    write_executive_summary(summary)
    return summary


def write_executive_summary(summary: dict[str, object]) -> None:
    md = f"""# Executive Summary

## Objective

Analyse online retail transaction lines to understand product sales structure, identify the strongest and weakest product opportunities, and create a practical next-quarter planning baseline.

## Dataset

- Analysis date: {summary["analysis_date"]}
- Clean transaction rows: {summary["clean_rows"]:,}
- Distinct orders: {summary["distinct_orders"]:,}
- Known customers: {summary["distinct_customers"]:,}
- Stock codes: {summary["stock_codes"]:,}
- Merchandise products: {summary["merchandise_products"]:,}
- Total clean revenue: {as_money(float(summary["total_revenue"]))}

## Key findings

- Product sales follow a long-tail pattern: the top 10 merchandise products contribute {as_pct(float(summary["top_10_revenue_share"]))} of merchandise revenue, while the top 500 contribute {as_pct(float(summary["top_500_revenue_share"]))}.
- Top revenue product: `{summary["top_revenue_product_description"]}` ({summary["top_revenue_product_code"]}), generating {as_money(float(summary["top_revenue_product_revenue"]))}.
- Top quantity product: `{summary["top_quantity_product_description"]}` ({summary["top_quantity_product_code"]}), with {summary["top_quantity_product_units"]:,} units sold.
- Broadest-reach product: `{summary["broad_demand_product_description"]}` ({summary["broad_demand_product_code"]}), appearing in {summary["broad_demand_product_orders"]:,} orders from {summary["broad_demand_product_customers"]:,} customers.
- Customer and purchase behaviour: {summary["repeat_customers"]:,} customers ({as_pct(float(summary["repeat_customer_share"]))}) placed at least two orders; the median order value is {as_money(float(summary["median_order_value"]))} and the median order contains {summary["median_units_per_order"]:,.0f} units.
- {summary["slow_moving_candidate_count"]} high-history-revenue merchandise products have not sold for at least 180 days and should be reviewed for clearance, bundling, relisting or delisting.
- Next-quarter baseline for {summary["forecast_product_count"]} stable high-revenue merchandise products: {summary["forecast_top_product_quantity"]:,.0f} units and {as_money(float(summary["forecast_top_product_revenue"]))} revenue in {summary["next_product_forecast_quarter"]}.
- Customer IDs support demand context, but the dataset does not contain demographic customer features such as age, gender or occupation.

## Recommended product actions

Protect stock availability for high-revenue products, use high-volume lower-revenue products for bundle and add-on opportunities, review slow-moving products before discounting or delisting, and use the next-quarter product forecast as a planning baseline rather than a final buying decision.

## Evidence for decision-makers

- [Product catalogue overview](../documentation/figures/product_catalog_overview.svg) shows catalogue breadth, active-month distribution and revenue concentration.
- [Customer and purchase behaviour](../documentation/figures/customer_purchase_overview.svg) shows repeat status, customer order frequency, order value and units per order.
- [Top products by revenue](../documentation/figures/top_products_by_revenue.svg) highlights the products driving income.
- [Top products by quantity](../documentation/figures/top_products_by_quantity.svg) highlights the products driving unit demand.
- [Slow-moving product candidates](../documentation/figures/slow_moving_products.svg) shows products with historical value but weak recent sales.
- [Next-quarter product forecast](../documentation/figures/product_forecast_next_quarter.svg) provides a simple planning baseline for stable high-revenue products.

## Forecasting note

The product forecast uses an average of the last four quarters and is limited to stable high-revenue merchandise products. It is designed as an interpretable planning baseline, not a production demand-forecasting model.
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


def shorten_label(value: object, max_chars: int = 42) -> str:
    text = str(value)
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def generate_figures(outputs: dict[str, pd.DataFrame], summary: dict[str, object]) -> None:
    """Create static, dependency-light SVG charts from the same SQL outputs as the dashboard."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Product catalogue overview.
    product_catalog = outputs.get("product_catalog_summary.csv")
    concentration = outputs.get("product_revenue_concentration.csv")
    if product_catalog is not None and concentration is not None:
        width, height = 1200, 760
        body = [
            chart_text(
                "Product catalogue after cleaning: broad assortment with a long revenue tail",
                55,
                48,
                20,
                weight="500",
            ),
            chart_text(
                f"{summary['merchandise_products']:,} merchandise products | Top 100 revenue share: {as_pct(float(summary['top_100_revenue_share']))} | Top 500 revenue share: {as_pct(float(summary['top_500_revenue_share']))}",
                55,
                76,
                13,
                fill="#5b6675",
            ),
        ]

        def bucket_panel(
            subset: pd.DataFrame,
            title: str,
            x0: int,
            y0: int,
            panel_width: int,
            panel_height: int,
            color: str,
        ) -> None:
            max_products = max(int(subset["products"].max()), 1)
            label_width = 116
            value_width = 112
            bar_x = x0 + label_width
            bar_width = panel_width - label_width - value_width - 18
            row_height = 24
            row_gap = 10
            body.append(
                f'<rect x="{x0 - 18}" y="{y0 - 35}" width="{panel_width + 26}" height="{panel_height}" rx="6" fill="#ffffff" stroke="#d9dee7" stroke-width="1"/>'
            )
            body.append(chart_text(title, x0, y0 - 10, 15, weight="500"))
            for index, row in enumerate(subset.itertuples(index=False)):
                y = y0 + 25 + index * (row_height + row_gap)
                products = int(row.products)
                share = float(row.product_share)
                bar_len = bar_width * products / max_products
                body.append(chart_text(row.bucket, x0, y + 17, 12, fill="#334155"))
                body.append(
                    f'<rect x="{bar_x}" y="{y}" width="{bar_width}" height="{row_height}" rx="4" fill="#eef2f7"/>'
                )
                body.append(
                    f'<rect x="{bar_x}" y="{y}" width="{bar_len:.1f}" height="{row_height}" rx="4" fill="{color}"/>'
                )
                body.append(
                    chart_text(
                        f"{products:,} ({share:.0%})",
                        bar_x + bar_width + 12,
                        y + 17,
                        12,
                        fill="#334155",
                    )
                )

        active_subset = product_catalog[product_catalog["feature"] == "active_months"]
        revenue_subset = product_catalog[product_catalog["feature"] == "total_revenue"]
        bucket_panel(active_subset, "Active months per product", 70, 145, 505, 300, "#2563eb")
        bucket_panel(revenue_subset, "Historical revenue per product", 665, 145, 505, 340, "#c2410c")

        concentration_subset = concentration[
            concentration["product_group"].isin(["Top 10", "Top 50", "Top 100", "Top 500"])
        ].copy()
        x0, y0, panel_width, panel_height = 70, 535, 1100, 170
        body.append(
            f'<rect x="{x0 - 18}" y="{y0 - 35}" width="{panel_width + 26}" height="{panel_height}" rx="6" fill="#ffffff" stroke="#d9dee7" stroke-width="1"/>'
        )
        body.append(chart_text("Revenue concentration", x0, y0 - 10, 15, weight="500"))
        max_share = max(float(concentration_subset["revenue_share"].max()), 1.0)
        bar_width = 820
        for index, row in enumerate(concentration_subset.itertuples(index=False)):
            y = y0 + 24 + index * 28
            share = float(row.revenue_share)
            body.append(chart_text(row.product_group, x0, y + 17, 12, fill="#334155"))
            body.append(
                f'<rect x="{x0 + 120}" y="{y}" width="{bar_width}" height="22" rx="4" fill="#eef2f7"/>'
            )
            body.append(
                f'<rect x="{x0 + 120}" y="{y}" width="{bar_width * share / max_share:.1f}" height="22" rx="4" fill="#0f766e"/>'
            )
            body.append(
                chart_text(
                    f"{as_pct(share)} | {int(row.products_in_group):,} products",
                    x0 + 955,
                    y + 16,
                    12,
                    fill="#334155",
                )
            )
        write_svg(
            FIGURES_DIR / "product_catalog_overview.svg",
            "Product catalogue overview",
            "Panels show merchandise product active-month distribution, historical revenue buckets and revenue concentration.",
            width,
            height,
            "".join(body),
        )

    # Customer and purchase behaviour overview.
    customer_profile = outputs.get("customer_profile_summary.csv")
    purchase_behavior = outputs.get("purchase_behavior_summary.csv")
    if customer_profile is not None and purchase_behavior is not None:
        width, height = 1200, 760
        body = [
            chart_text(
                "Customer and purchase behaviour after cleaning",
                55,
                48,
                20,
                weight="500",
            ),
            chart_text(
                f"{summary['distinct_customers']:,} known customers | {summary['distinct_orders']:,} completed orders | median order value: {as_money(float(summary['median_order_value']))}",
                55,
                76,
                13,
                fill="#5b6675",
            ),
        ]

        def distribution_panel(
            subset: pd.DataFrame,
            title: str,
            x0: int,
            y0: int,
            panel_width: int,
            panel_height: int,
            count_col: str,
            share_col: str,
            color: str,
        ) -> None:
            max_count = max(int(subset[count_col].max()), 1)
            label_width = 116
            value_width = 120
            bar_x = x0 + label_width
            bar_width = panel_width - label_width - value_width - 18
            row_height = 24
            row_gap = 9
            body.append(
                f'<rect x="{x0 - 18}" y="{y0 - 35}" width="{panel_width + 26}" height="{panel_height}" rx="6" fill="#ffffff" stroke="#d9dee7" stroke-width="1"/>'
            )
            body.append(chart_text(title, x0, y0 - 10, 15, weight="500"))
            for index, row in enumerate(subset.itertuples(index=False)):
                y = y0 + 25 + index * (row_height + row_gap)
                row_dict = row._asdict()
                count = int(row_dict[count_col])
                share = float(row_dict[share_col])
                bar_len = bar_width * count / max_count
                body.append(chart_text(row_dict["bucket"], x0, y + 17, 12, fill="#334155"))
                body.append(
                    f'<rect x="{bar_x}" y="{y}" width="{bar_width}" height="{row_height}" rx="4" fill="#eef2f7"/>'
                )
                body.append(
                    f'<rect x="{bar_x}" y="{y}" width="{bar_len:.1f}" height="{row_height}" rx="4" fill="{color}"/>'
                )
                body.append(
                    chart_text(
                        f"{count:,} ({share:.0%})",
                        bar_x + bar_width + 12,
                        y + 17,
                        12,
                        fill="#334155",
                    )
                )

        distribution_panel(
            customer_profile[customer_profile["feature"] == "repeat_status"],
            "Customer repeat status",
            70,
            145,
            505,
            160,
            "customers",
            "customer_share",
            "#2563eb",
        )
        distribution_panel(
            customer_profile[customer_profile["feature"] == "total_orders"],
            "Orders per customer",
            665,
            145,
            505,
            290,
            "customers",
            "customer_share",
            "#0f766e",
        )
        distribution_panel(
            purchase_behavior[purchase_behavior["feature"] == "order_value"],
            "Order value",
            70,
            455,
            505,
            250,
            "orders",
            "order_share",
            "#c2410c",
        )
        distribution_panel(
            purchase_behavior[purchase_behavior["feature"] == "units_purchased"],
            "Units per order",
            665,
            455,
            505,
            250,
            "orders",
            "order_share",
            "#7c3aed",
        )

        write_svg(
            FIGURES_DIR / "customer_purchase_overview.svg",
            "Customer and purchase behaviour overview",
            "Panels show repeat status, orders per customer, order value and units per order.",
            width,
            height,
            "".join(body),
        )

    def write_product_top_chart(
        df: pd.DataFrame,
        value_col: str,
        title: str,
        filename: str,
        color: str,
        formatter,
    ) -> None:
        chart_df = df.head(10).iloc[::-1].reset_index(drop=True)
        width, height = 1200, 620
        left, right, top, bottom = 365, 185, 88, 70
        plot_width = width - left - right
        row_height, gap = 34, 16
        max_value = max(float(chart_df[value_col].max()), 1.0)
        body = [chart_text(title, 55, 45, 20, weight="500")]
        for index, row in enumerate(chart_df.itertuples(index=False)):
            y = top + index * (row_height + gap)
            value = float(getattr(row, value_col))
            label = f"{row.stock_code} | {shorten_label(row.product_description, 42)}"
            bar_width = plot_width * value / max_value
            body.append(chart_text(label, left - 16, y + 23, 12, anchor="end"))
            body.append(
                f'<rect x="{left}" y="{y}" width="{plot_width}" height="{row_height}" rx="4" fill="#eef2f7"/>'
            )
            body.append(
                f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="{row_height}" rx="4" fill="{color}"/>'
            )
            body.append(chart_text(formatter(value), left + bar_width + 12, y + 23, 12))
        write_svg(
            FIGURES_DIR / filename,
            title,
            f"Horizontal bar chart for {title}.",
            width,
            height,
            "".join(body),
        )

    if "top_products_by_revenue.csv" in outputs:
        write_product_top_chart(
            outputs["top_products_by_revenue.csv"],
            "total_revenue",
            "Top 10 merchandise products by revenue",
            "top_products_by_revenue.svg",
            "#c2410c",
            lambda value: as_money(value),
        )

    if "top_products_by_quantity.csv" in outputs:
        write_product_top_chart(
            outputs["top_products_by_quantity.csv"],
            "total_quantity",
            "Top 10 merchandise products by units sold",
            "top_products_by_quantity.svg",
            "#2563eb",
            lambda value: f"{value:,.0f} units",
        )

    if "slow_moving_product_candidates.csv" in outputs:
        slow_df = outputs["slow_moving_product_candidates.csv"].head(10).iloc[::-1]
        width, height = 1200, 620
        left, right, top, bottom = 365, 220, 88, 70
        plot_width = width - left - right
        max_value = max(float(slow_df["total_revenue"].max()), 1.0)
        body = [
            chart_text(
                "Slow-moving product candidates: historical value but no sale for 180+ days",
                55,
                45,
                20,
                weight="500",
            )
        ]
        for index, row in enumerate(slow_df.itertuples(index=False)):
            y = top + index * 50
            value = float(row.total_revenue)
            bar_width = plot_width * value / max_value
            label = f"{row.stock_code} | {shorten_label(row.product_description, 42)}"
            body.append(chart_text(label, left - 16, y + 23, 12, anchor="end"))
            body.append(
                f'<rect x="{left}" y="{y}" width="{plot_width}" height="34" rx="4" fill="#eef2f7"/>'
            )
            body.append(
                f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="34" rx="4" fill="#7c3aed"/>'
            )
            body.append(
                chart_text(
                    f"{as_money(value)} | {int(row.days_since_last_sale)} days",
                    left + bar_width + 12,
                    y + 23,
                    12,
                )
            )
        write_svg(
            FIGURES_DIR / "slow_moving_products.svg",
            "Slow-moving product candidates",
            "Products with at least GBP 5k historical revenue and at least 180 days since last sale.",
            width,
            height,
            "".join(body),
        )

    if "product_next_quarter_forecast.csv" in outputs:
        forecast_df = outputs["product_next_quarter_forecast.csv"].head(10).iloc[::-1]
        width, height = 1200, 620
        left, right, top, bottom = 365, 200, 88, 70
        plot_width = width - left - right
        max_value = max(float(forecast_df["forecast_revenue"].max()), 1.0)
        quarter_label = forecast_df["next_quarter"].iloc[0] if not forecast_df.empty else "next quarter"
        body = [
            chart_text(
                f"Next-quarter revenue baseline for stable high-revenue products ({quarter_label})",
                55,
                45,
                20,
                weight="500",
            )
        ]
        for index, row in enumerate(forecast_df.itertuples(index=False)):
            y = top + index * 50
            value = float(row.forecast_revenue)
            bar_width = plot_width * value / max_value
            label = f"{row.stock_code} | {shorten_label(row.product_description, 42)}"
            body.append(chart_text(label, left - 16, y + 23, 12, anchor="end"))
            body.append(
                f'<rect x="{left}" y="{y}" width="{plot_width}" height="34" rx="4" fill="#eef2f7"/>'
            )
            body.append(
                f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="34" rx="4" fill="#0f766e"/>'
            )
            body.append(
                chart_text(
                    f"{as_money(value)} | {float(row.forecast_quantity):,.0f} units",
                    left + bar_width + 12,
                    y + 23,
                    12,
                )
            )
        write_svg(
            FIGURES_DIR / "product_forecast_next_quarter.svg",
            "Next-quarter product forecast",
            "Last-four-quarter average forecast for stable high-revenue merchandise products.",
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
    monthly_body = [chart_text("Monthly sales trend provides context before product planning", 80, 42, 19, weight="500")]
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
        monthly["orders"].astype(float).tolist(),
        monthly_labels,
        105,
        375,
        900,
        250,
        "Monthly orders",
        "#0f766e",
        lambda value: f"{value:,.0f}",
    )
    write_svg(
        FIGURES_DIR / "monthly_kpis.svg",
        "Monthly sales and order trend",
        "Two line charts show monthly revenue and completed orders.",
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
    top_revenue = outputs["top_products_by_revenue.csv"].copy()
    top_quantity = outputs["top_products_by_quantity.csv"].copy()
    slow = outputs["slow_moving_product_candidates.csv"].head(12).copy()
    forecast = outputs["product_next_quarter_forecast.csv"].head(12).copy()
    concentration = outputs["product_revenue_concentration.csv"].copy()

    top_revenue_table = top_revenue[
        [
            "stock_code",
            "product_description",
            "total_revenue",
            "total_quantity",
            "order_count",
            "customer_count",
        ]
    ].copy()
    top_revenue_table["total_revenue"] = top_revenue_table["total_revenue"].map(
        lambda x: as_money(float(x))
    )

    top_quantity_table = top_quantity[
        [
            "stock_code",
            "product_description",
            "total_quantity",
            "total_revenue",
            "order_count",
            "customer_count",
        ]
    ].copy()
    top_quantity_table["total_revenue"] = top_quantity_table["total_revenue"].map(
        lambda x: as_money(float(x))
    )

    slow_table = slow[
        [
            "stock_code",
            "product_description",
            "total_revenue",
            "days_since_last_sale",
            "active_months",
        ]
    ].copy()
    slow_table["total_revenue"] = slow_table["total_revenue"].map(
        lambda x: as_money(float(x))
    )

    forecast_table = forecast[
        [
            "stock_code",
            "product_description",
            "next_quarter",
            "forecast_quantity",
            "forecast_revenue",
        ]
    ].copy()
    forecast_table["forecast_revenue"] = forecast_table["forecast_revenue"].map(
        lambda x: as_money(float(x))
    )

    concentration_table = concentration.copy()
    concentration_table["group_revenue"] = concentration_table["group_revenue"].map(
        lambda x: as_money(float(x))
    )
    concentration_table["revenue_share"] = concentration_table["revenue_share"].map(
        lambda x: as_pct(float(x))
    )

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Online Retail Product Sales Dashboard</title>
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
    <h1>Online Retail Product Sales Dashboard</h1>
    <p>Product performance, top sellers, slow-moving candidates and next-quarter planning baseline.</p>
  </header>
  <main>
    <div class="kpi-grid">
      <div class="kpi"><div class="kpi-title">Total Revenue</div><div class="kpi-value">{as_money(float(summary["total_revenue"]))}</div></div>
      <div class="kpi"><div class="kpi-title">Merchandise Products</div><div class="kpi-value">{int(summary["merchandise_products"]):,}</div></div>
      <div class="kpi"><div class="kpi-title">Orders</div><div class="kpi-value">{int(summary["distinct_orders"]):,}</div></div>
      <div class="kpi"><div class="kpi-title">Top 500 Revenue Share</div><div class="kpi-value">{as_pct(float(summary["top_500_revenue_share"]))}</div></div>
    </div>

    <div class="figure-grid">
      <section>
        <h2>Catalogue Structure</h2>
        <figure><img src="../documentation/figures/product_catalog_overview.svg" alt="Product catalogue overview"></figure>
      </section>
      <section>
        <h2>Customer and Purchase Behaviour</h2>
        <figure><img src="../documentation/figures/customer_purchase_overview.svg" alt="Customer and purchase behaviour overview"></figure>
      </section>
      <section>
        <h2>Monthly Sales Trend</h2>
        <figure><img src="../documentation/figures/monthly_kpis.svg" alt="Monthly sales and order trend"></figure>
      </section>
      <section>
        <h2>Next-Quarter Baseline</h2>
        <figure><img src="../documentation/figures/product_forecast_next_quarter.svg" alt="Next-quarter product forecast"></figure>
      </section>
    </div>

    <section>
      <h2>Revenue Concentration</h2>
      {table_html(concentration_table, max_rows=5)}
      <div class="note">Service and administrative stock lines are excluded from merchandise revenue concentration.</div>
    </section>

    <div class="grid-2">
      <section>
        <h2>Top Products by Revenue</h2>
        <figure><img src="../documentation/figures/top_products_by_revenue.svg" alt="Top products by revenue"></figure>
        {table_html(top_revenue_table, max_rows=10)}
      </section>
      <section>
        <h2>Top Products by Units Sold</h2>
        <figure><img src="../documentation/figures/top_products_by_quantity.svg" alt="Top products by units sold"></figure>
        {table_html(top_quantity_table, max_rows=10)}
      </section>
    </div>

    <div class="grid-2">
      <section>
        <h2>Slow-Moving Product Candidates</h2>
        <figure><img src="../documentation/figures/slow_moving_products.svg" alt="Slow-moving product candidates"></figure>
        {table_html(slow_table, max_rows=12)}
      </section>
      <section>
        <h2>Forecast Table</h2>
        {table_html(forecast_table, max_rows=12)}
        <div class="note">Forecast uses the average of the last four quarters for stable high-revenue merchandise products.</div>
      </section>
    </div>

    <section>
      <h2>Product Actions</h2>
      <p>Protect availability for high-revenue products, use high-unit lower-revenue products for bundles and add-ons, review slow-moving products before discounting or delisting, and treat the forecast as a planning baseline rather than a final buying decision.</p>
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
    outputs["customer_profile_summary.csv"] = generate_customer_profile_summary(outputs)
    outputs["purchase_behavior_summary.csv"] = generate_purchase_behavior_summary(outputs)
    outputs.update(generate_product_report_outputs(outputs))
    outputs["product_next_quarter_forecast.csv"] = generate_product_quarterly_forecast(outputs)
    summary = generate_summary(outputs)
    generate_figures(outputs, summary)
    generate_dashboard(outputs, summary)

    print("Generated project outputs:")
    for csv_name in QUERY_OUTPUTS.values():
        print(f"- {OUTPUT_DIR / csv_name}")
    print(f"- {OUTPUT_DIR / 'monthly_forecast.csv'}")
    print(f"- {OUTPUT_DIR / 'customer_profile_summary.csv'}")
    print(f"- {OUTPUT_DIR / 'purchase_behavior_summary.csv'}")
    for csv_name in (
        "top_products_by_quantity.csv",
        "top_products_by_revenue.csv",
        "product_catalog_summary.csv",
        "slow_moving_product_candidates.csv",
        "product_next_quarter_forecast.csv",
    ):
        print(f"- {OUTPUT_DIR / csv_name}")
    print(f"- {OUTPUT_DIR / 'executive_summary.md'}")
    for figure_name in (
        "product_catalog_overview.svg",
        "customer_purchase_overview.svg",
        "top_products_by_revenue.svg",
        "top_products_by_quantity.svg",
        "slow_moving_products.svg",
        "product_forecast_next_quarter.svg",
        "monthly_kpis.svg",
        "monthly_forecast.svg",
    ):
        print(f"- {FIGURES_DIR / figure_name}")
    print(f"- {DASHBOARD_DIR / 'customer_retention_dashboard.html'}")


if __name__ == "__main__":
    main()
