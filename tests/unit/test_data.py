import pandas as pd
import pytest

from processor.data import (
    compute_hum_domain,
    compute_temp_domain,
    resample_for_display,
    rolling_median,
    x_format,
)

_FIXTURES_DIR = str(__file__).replace("tests/unit/test_data.py", "tests/fixtures")


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_indexed_df(start: str, end: str, freq: str = "5min") -> pd.DataFrame:
    idx = pd.date_range(start=start, end=end, freq=freq)
    return pd.DataFrame(
        {"temperature_c": 25.0, "humidity_pct": 50.0},
        index=idx,
    )


def _median_interval_minutes(df: pd.DataFrame) -> float:
    return df.index.to_series().diff().dropna().median().total_seconds() / 60


# ── resample_for_display ──────────────────────────────────────────────────────

class TestResampleForDisplay:
    def test_1day_span_uses_5min(self):
        df = _make_indexed_df("2026-01-01", "2026-01-02")
        result = resample_for_display(df)
        assert _median_interval_minutes(result) == 5

    def test_3day_span_uses_30min(self):
        df = _make_indexed_df("2026-01-01", "2026-01-03")
        result = resample_for_display(df)
        assert _median_interval_minutes(result) == 30

    def test_7day_span_uses_1h(self):
        df = _make_indexed_df("2026-01-01", "2026-01-05")  # 4-day span
        result = resample_for_display(df)
        assert _median_interval_minutes(result) == 60

    def test_30day_span_uses_6h(self):
        df = _make_indexed_df("2026-01-01", "2026-01-15", freq="1h")  # 14-day span
        result = resample_for_display(df)
        assert _median_interval_minutes(result) == 360

    def test_over_30day_span_uses_1day(self):
        df = _make_indexed_df("2026-01-01", "2026-04-01", freq="1h")  # 90-day span
        result = resample_for_display(df)
        assert _median_interval_minutes(result) == 60 * 24

    def test_single_row_returned_as_is(self):
        idx = pd.date_range("2026-01-01", periods=1, freq="5min")
        df = pd.DataFrame({"temperature_c": [25.0], "humidity_pct": [50.0]}, index=idx)
        result = resample_for_display(df)
        assert len(result) == 1

    def test_output_averages_values(self):
        idx = pd.date_range("2026-01-01 00:00", periods=10, freq="1min")
        temps = [20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0]
        df = pd.DataFrame({"temperature_c": temps, "humidity_pct": 50.0}, index=idx)
        result = resample_for_display(df)
        # first 5-min bin should average the first 5 values
        expected = sum(temps[:5]) / 5
        assert result["temperature_c"].iloc[0] == pytest.approx(expected)


# ── x_format ─────────────────────────────────────────────────────────────────

class TestXFormat:
    def test_1day(self):
        assert x_format(1) == "%H:%M"

    def test_3day(self):
        assert x_format(3) == "%m/%d(%a) %H時"

    def test_7day(self):
        assert x_format(7) == "%m/%d(%a) %H時"

    def test_30day(self):
        assert x_format(30) == "%m/%d"

    def test_365day(self):
        assert x_format(365) == "%Y/%m"

    def test_boundary_just_over_1day(self):
        assert x_format(1.1) == "%m/%d(%a) %H時"

    def test_boundary_just_over_7day(self):
        assert x_format(7.1) == "%m/%d"


# ── compute_temp_domain ───────────────────────────────────────────────────────

class TestComputeTempDomain:
    def _df(self, temps: list[float]) -> pd.DataFrame:
        idx = pd.date_range("2026-01-01", periods=len(temps), freq="5min")
        return pd.DataFrame({"temperature_c": temps, "humidity_pct": 50.0}, index=idx)

    def test_domain_adds_half_degree_padding(self):
        df = self._df([20.0, 25.0, 30.0])
        lo, hi = compute_temp_domain(df)
        assert lo == pytest.approx(19.5)
        assert hi == pytest.approx(30.5)

    def test_domain_with_single_value(self):
        df = self._df([24.0])
        lo, hi = compute_temp_domain(df)
        assert lo == pytest.approx(23.5)
        assert hi == pytest.approx(24.5)


# ── compute_hum_domain ────────────────────────────────────────────────────────

class TestComputeHumDomain:
    def _df(self, hums: list[float]) -> pd.DataFrame:
        idx = pd.date_range("2026-01-01", periods=len(hums), freq="5min")
        return pd.DataFrame({"temperature_c": 25.0, "humidity_pct": hums}, index=idx)

    def test_domain_adds_5pct_padding(self):
        df = self._df([40.0, 55.0, 70.0])
        lo, hi = compute_hum_domain(df)
        assert lo == pytest.approx(35.0)
        assert hi == pytest.approx(75.0)

    def test_domain_with_single_value(self):
        df = self._df([50.0])
        lo, hi = compute_hum_domain(df)
        assert lo == pytest.approx(45.0)
        assert hi == pytest.approx(55.0)


# ── rolling_median ────────────────────────────────────────────────────────────

class TestRollingMedian:
    def _df(self, temps: list[float]) -> pd.DataFrame:
        idx = pd.date_range("2026-01-01", periods=len(temps), freq="5min")
        return pd.DataFrame({"temperature_c": temps, "humidity_pct": 50.0}, index=idx)

    def test_suppresses_single_outlier(self):
        temps = [24.0] * 12 + [50.0] + [24.0] * 12
        result = rolling_median(self._df(temps), window="1h")
        assert result["temperature_c"].iloc[12] == pytest.approx(24.0)

    def test_preserves_stable_values(self):
        result = rolling_median(self._df([24.0] * 24), window="1h")
        assert (result["temperature_c"] == 24.0).all()

    def test_follows_sustained_change(self):
        temps = [24.0] * 12 + [26.0] * 24
        result = rolling_median(self._df(temps), window="1h")
        assert result["temperature_c"].iloc[-1] == pytest.approx(26.0)

    def test_empty_df_returns_empty(self):
        df = pd.DataFrame(columns=["temperature_c", "humidity_pct"])
        assert rolling_median(df).empty
