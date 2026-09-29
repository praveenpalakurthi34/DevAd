import pytest
from app.api.outcomes import calculate_metrics


def test_calculate_metrics_normal():
    metrics = calculate_metrics(100000, 5000, 250, 1000.0, 5000.0)
    assert metrics["ctr"] == 5.0
    assert metrics["cvr"] == 5.0
    assert metrics["cpa"] == 4.0
    assert metrics["roas"] == 5.0


def test_calculate_metrics_zero_impressions():
    metrics = calculate_metrics(0, 0, 0, 100.0, 0.0)
    assert "ctr" not in metrics


def test_calculate_metrics_zero_clicks():
    metrics = calculate_metrics(1000, 0, 0, 100.0, 0.0)
    assert "cvr" not in metrics


def test_calculate_metrics_zero_conversions():
    metrics = calculate_metrics(1000, 100, 0, 100.0, 0.0)
    assert "cpa" not in metrics


def test_calculate_metrics_zero_spend():
    metrics = calculate_metrics(1000, 100, 10, 0, 500.0)
    assert "roas" not in metrics


def test_calculate_metrics_none_values():
    metrics = calculate_metrics(None, None, None, None, None)
    assert len(metrics) == 0
