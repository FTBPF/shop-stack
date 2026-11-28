import pandas as pd
import pytest

from shop_stack import reports


def test_revenue(built_warehouse):
    result = reports.run_report(built_warehouse, "revenue")

    actual = {
        row.month_start.strftime("%Y-%m"): float(row.revenue)
        for row in result.itertuples()
    }

    assert actual == {
        "2025-01": 88.00,
        "2025-02": 80.00,
        "2025-03": 208.00,
    }

    assert result["revenue"].sum() == pytest.approx(376.00)


def test_margin(built_warehouse):
    result = reports.run_report(built_warehouse, "margin")

    actual = {
        row.month_start.strftime("%Y-%m"): float(row.gross_margin)
        for row in result.itertuples()
    }
    
    assert actual == {
            "2025-01": 53.00,
            "2025-02": 47.00,
            "2025-03": 123.00,
    }

    assert result["gross_margin"].sum() == pytest.approx(223.00)


def test_returns(built_warehouse):
    result = reports.run_report(built_warehouse, "returns")

    actual = {
        row.category: row.return_rate_pct
        for row in result.itertuples()
    }

    assert actual == {
        "Jeans": 0.0,
        "Outerwear & Coats": 50.0,
        "Socks": 0.0,
        "Tops & Tees": 0.0,
    }


def test_sources(built_warehouse):
    result = reports.run_report(built_warehouse, "sources")

    actual = {
        row.traffic_source: float(row.revenue)
        for row in result.itertuples()
    }

    assert actual == {
        "Search": 176.00,
        "Organic": 140.00,
        "Email": 60.00,
        "Facebook": 0.00,
    }


def test_retention(built_warehouse):
    result = reports.run_report(built_warehouse, "retention")

    actual = {
        (
            row.cohort_month.strftime("%Y-%m"),
            row.months_since_cohort,
        ): (
            row.customer_count,
            row.returning_customers,
            row.retention_pct,
        )
        for row in result.itertuples()
    }

    assert actual == {
        ("2025-01", 1): (2, 1, 50.0),
        ("2025-01", 2): (2, 2, 100.0),
        ("2025-02", 1): (1, 1, 100.0),
        ("2025-03", None): (1, None, None),
    }


def test_funnel(built_warehouse):
    result = reports.run_report(built_warehouse, "funnel")

    actual = {
        row.stage: 
        (
            row.session_count,
            round(row.from_previous_stage_pct, 1),
            round(row.overall_pct, 1),
        )
        for row in result.itertuples()
    }

    assert actual == {
        "sessions": (7, 100.0, 100.0),
        "product": (5, 71.4, 71.4),
        "cart": (4, 80.0, 57.1),
        "purchase": (3, 75.0, 42.9),
    }
