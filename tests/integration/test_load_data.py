import os

import pandas as pd
import pytest

from processor.data import load_data

_FIXTURES = os.path.join(os.path.dirname(__file__), "../fixtures")


class TestLoadDataFormats:
    def test_new_format_columns_loaded(self):
        df = load_data(_FIXTURES)
        assert list(df.columns) == ["timestamp", "temperature_c", "humidity_pct"]

    def test_new_format_values(self):
        df = load_data(_FIXTURES)
        row = df[df["timestamp"] == pd.Timestamp("2026-05-01 00:00:00")].iloc[0]
        assert row["temperature_c"] == pytest.approx(24.0)
        assert row["humidity_pct"] == pytest.approx(50.0)

    def test_old_format_renamed_correctly(self):
        # old_format.csv uses Timestamp / Temperature (℃) / Humidity (%)
        df = load_data(_FIXTURES)
        row = df[df["timestamp"] == pd.Timestamp("2025-05-01 00:00:00")].iloc[0]
        assert row["temperature_c"] == pytest.approx(25.0)
        assert row["humidity_pct"] == pytest.approx(55.0)

    def test_both_formats_combined(self):
        df = load_data(_FIXTURES)
        # fixtures/ contains new_format.csv (5 rows) + old_format.csv (4 rows)
        assert len(df) == 9


class TestLoadDataSorting:
    def test_sorted_ascending_by_timestamp(self, tmp_path):
        (tmp_path / "unsorted.csv").write_text(
            "timestamp,temperature_c,humidity_pct\n"
            "2026-03-02 00:00:00,25.0,50.0\n"
            "2026-03-01 00:00:00,24.0,49.0\n"
        )
        df = load_data(str(tmp_path))
        assert df["timestamp"].iloc[0] < df["timestamp"].iloc[1]

    def test_timestamp_column_is_datetime(self, tmp_path):
        (tmp_path / "t.csv").write_text(
            "timestamp,temperature_c,humidity_pct\n"
            "2026-01-01 00:00:00,24.0,50.0\n"
        )
        df = load_data(str(tmp_path))
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])


class TestLoadDataEdgeCases:
    def test_empty_dir_returns_empty_dataframe(self, tmp_path):
        df = load_data(str(tmp_path))
        assert df.empty
        assert list(df.columns) == ["timestamp", "temperature_c", "humidity_pct"]

    def test_corrupted_file_does_not_crash(self, tmp_path):
        (tmp_path / "bad.csv").write_bytes(b"\xff\xfe broken content")
        (tmp_path / "good.csv").write_text(
            "timestamp,temperature_c,humidity_pct\n"
            "2026-01-01 00:00:00,24.0,50.0\n"
        )
        df = load_data(str(tmp_path))
        assert len(df) == 1

    def test_invalid_timestamps_dropped(self, tmp_path):
        (tmp_path / "t.csv").write_text(
            "timestamp,temperature_c,humidity_pct\n"
            "not-a-date,24.0,50.0\n"
            "2026-01-01 00:00:00,25.0,51.0\n"
        )
        df = load_data(str(tmp_path))
        assert len(df) == 1
        assert df["timestamp"].iloc[0] == pd.Timestamp("2026-01-01 00:00:00")

    def test_file_without_timestamp_column_skipped(self, tmp_path):
        (tmp_path / "wrong.csv").write_text("col_a,col_b\n1,2\n")
        df = load_data(str(tmp_path))
        assert df.empty
