import numpy as np
import pandas as pd

from automation.detector import detect_cycling


def _series(temps: list[float], freq: str = "5min") -> pd.Series:
    idx = pd.date_range("2026-07-20 00:00", periods=len(temps), freq=freq)
    return pd.Series(temps, index=idx, name="temperature_c")


def _sawtooth(hours: float = 3, amplitude: float = 1.5) -> pd.Series:
    """サーモスタットサイクルを模した波形(40分周期、山谷で1サンプル滞留)。"""
    up = [24.0 + amplitude * f for f in (1 / 3, 2 / 3, 1.0, 1.0)]
    down = [24.0 + amplitude * f for f in (2 / 3, 1 / 3, 0.0, 0.0)]
    period = up + down
    n = int(hours * 60 / 5)
    return _series((period * (n // len(period) + 1))[:n])


class TestDetectCycling:
    def test_sawtooth_is_detected(self):
        result = detect_cycling(_sawtooth())
        assert result.cycling
        assert result.swing_count >= 4

    def test_flat_is_not_detected(self):
        result = detect_cycling(_series([24.0] * 36))
        assert not result.cycling
        assert result.swing_count == 0

    def test_single_bump_is_not_detected(self):
        temps = [24.0] * 12 + [24.3, 24.6, 25.0, 25.2, 25.0, 24.6, 24.3] + [24.0] * 17
        result = detect_cycling(_series(temps))
        assert not result.cycling

    def test_isolated_spikes_are_not_detected(self):
        # DHT-11 の単発外れ値が繰り返し出ても presmooth で除去される
        temps = [24.0] * 36
        for i in (6, 18, 30):
            temps[i] = 27.0
        result = detect_cycling(_series(temps))
        assert not result.cycling
        assert result.swing_count == 0

    def test_small_noise_is_not_detected(self):
        rng = np.random.default_rng(1)
        temps = list(24.0 + rng.normal(0, 0.15, 36))
        result = detect_cycling(_series(temps))
        assert not result.cycling

    def test_nan_values_are_ignored(self):
        s = _sawtooth()
        s.iloc[::7] = np.nan
        assert detect_cycling(s).cycling

    def test_too_few_samples_returns_not_cycling(self):
        assert not detect_cycling(_series([24.0, 25.0])).cycling

    def test_amplitude_threshold_is_respected(self):
        # 振幅 0.5℃ のサイクルは閾値 0.8℃ では検出しない
        result = detect_cycling(_sawtooth(amplitude=0.5), min_amplitude_c=0.8)
        assert not result.cycling
