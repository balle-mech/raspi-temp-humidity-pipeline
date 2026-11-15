"""api.readings: 日次 CSV から「ある時刻より後」の計測値を読む。"""

from datetime import datetime
from pathlib import Path

from api.readings import read_since

NEW = "timestamp,temperature_c,humidity_pct\n"
OLD = "Timestamp,Temperature (℃),Humidity (%)\n"


def write(root: Path, day: str, body: str, header: str = NEW) -> None:
    y, m, _ = day.split("-")
    p = root / y / m / f"temp_humidity_{day}.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(header + body, encoding="utf-8")


def test_returns_rows_after_since_in_order(tmp_path):
    write(tmp_path, "2026-11-14", "2026-11-14 23:55:00,20.0,50.0\n")
    write(tmp_path, "2026-11-15", "2026-11-15 00:00:00,20.5,51.0\n2026-11-15 00:05:00,21.0,52.0\n")
    rows, more = read_since(tmp_path, datetime(2026, 11, 14, 23, 55))
    assert [r["timestamp"] for r in rows] == ["2026-11-15 00:00:00", "2026-11-15 00:05:00"]
    assert rows[0] == {"timestamp": "2026-11-15 00:00:00", "temperature_c": 20.5, "humidity_pct": 51.0}
    assert more is False


def test_none_since_returns_everything_including_old_format(tmp_path):
    write(tmp_path, "2025-05-01", "2025-05-01 00:00:00,25,55\n", header=OLD)
    write(tmp_path, "2026-11-15", "2026-11-15 00:00:00,20.5,51.0\n")
    rows, _ = read_since(tmp_path, None)
    assert [r["temperature_c"] for r in rows] == [25.0, 20.5]


def test_failed_reading_is_null(tmp_path):
    write(tmp_path, "2026-11-15", "2026-11-15 00:00:00,,\n")
    [r], _ = read_since(tmp_path, None)
    assert (r["temperature_c"], r["humidity_pct"]) == (None, None)


def test_limit_sets_more(tmp_path):
    write(tmp_path, "2026-11-15", "".join(f"2026-11-15 00:{m:02d}:00,20,50\n" for m in range(0, 30, 5)))
    rows, more = read_since(tmp_path, None, limit=4)
    assert len(rows) == 4 and more is True
    rest, more = read_since(tmp_path, datetime.fromisoformat(rows[-1]["timestamp"]), limit=4)
    assert len(rest) == 2 and more is False


def test_broken_lines_are_skipped(tmp_path):
    write(tmp_path, "2026-11-15", "壊れた行\n2026-11-15 00:00:00,20,50\n")
    rows, _ = read_since(tmp_path, None)
    assert len(rows) == 1


def test_duplicate_timestamp_with_empty_value_does_not_crash(tmp_path):
    # 同じ時刻の行が2つあり、片方の温度が空でも落ちない（並べ替えで None と数値を比べない）
    write(tmp_path, "2026-11-16", "2026-11-16 08:00:00,,50.0\n2026-11-16 08:00:00,20.0,50.0\n2026-11-16 08:05:00,21.0,51.0\n")
    rows, _ = read_since(tmp_path, None)
    assert [r["timestamp"] for r in rows] == ["2026-11-16 08:00:00", "2026-11-16 08:00:00", "2026-11-16 08:05:00"]


def test_unreadable_file_is_skipped(tmp_path):
    # UTF-8 でない CSV が混ざっていても、他のファイルは返す
    write(tmp_path, "2026-11-16", "2026-11-16 08:00:00,20.0,50.0\n")
    (tmp_path / "broken.csv").write_bytes("timestamp,温度\n".encode("shift_jis") + b"\xff\xfe\n")
    rows, _ = read_since(tmp_path, None)
    assert [r["timestamp"] for r in rows] == ["2026-11-16 08:00:00"]
