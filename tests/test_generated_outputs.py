from __future__ import annotations

import math
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DASHBOARD_PATH = PROJECT_ROOT / "dashboard" / "product_sales_dashboard.html"


class GeneratedOutputTests(unittest.TestCase):
    def test_required_outputs_exist(self) -> None:
        required_files = [
            "dataset_overview.csv",
            "data_quality_checks.csv",
            "product_performance.csv",
            "product_revenue_concentration.csv",
            "country_sales_context.csv",
            "product_next_quarter_forecast.csv",
            "product_forecast_backtest.csv",
            "top_products_by_revenue.csv",
            "top_products_by_quantity.csv",
            "slow_moving_product_candidates.csv",
            "portfolio_metrics.json",
        ]
        missing = [name for name in required_files if not (OUTPUT_DIR / name).exists()]
        self.assertEqual(missing, [])

    def test_data_quality_checks_pass(self) -> None:
        checks = pd.read_csv(OUTPUT_DIR / "data_quality_checks.csv")
        self.assertGreaterEqual(len(checks), 6)
        self.assertTrue((checks["status"] == "Pass").all())

    def test_country_revenue_reconciles_to_dataset_revenue(self) -> None:
        overview = pd.read_csv(OUTPUT_DIR / "dataset_overview.csv").iloc[0]
        countries = pd.read_csv(OUTPUT_DIR / "country_sales_context.csv")
        self.assertGreaterEqual(len(countries), 1)
        self.assertAlmostEqual(
            float(overview["total_revenue"]),
            float(countries["revenue"].sum()),
            places=2,
        )

    def test_forecast_and_backtest_are_usable(self) -> None:
        forecast = pd.read_csv(OUTPUT_DIR / "product_next_quarter_forecast.csv")
        backtest = pd.read_csv(OUTPUT_DIR / "product_forecast_backtest.csv")

        self.assertEqual(len(forecast), 20)
        self.assertEqual(len(backtest), 20)
        self.assertTrue((forecast["forecast_revenue"] > 0).all())
        self.assertTrue((forecast["forecast_quantity"] > 0).all())
        self.assertTrue((backtest["validation_quarters"] > 0).all())
        self.assertTrue(backtest["revenue_mape"].map(math.isfinite).all())

    def test_dashboard_is_visual_first(self) -> None:
        dashboard = DASHBOARD_PATH.read_text(encoding="utf-8").lower()
        self.assertIn("<svg", dashboard)
        self.assertIn("forecast backtest", dashboard)
        self.assertIn("geographic sales context", dashboard)
        self.assertNotIn("<table", dashboard)


if __name__ == "__main__":
    unittest.main()
