from datetime import datetime

from automation.presence import last_motion, record_motion

_TS = datetime(2026, 7, 20, 12, 34, 56)


class TestPresenceStateFile:
    def test_roundtrip(self, tmp_path):
        path = tmp_path / "state" / "last_motion"
        record_motion(path, _TS)
        assert last_motion(path) == _TS

    def test_missing_file_returns_none(self, tmp_path):
        assert last_motion(tmp_path / "nonexistent") is None

    def test_corrupt_file_returns_none(self, tmp_path):
        path = tmp_path / "last_motion"
        path.write_text("not-a-timestamp")
        assert last_motion(path) is None
