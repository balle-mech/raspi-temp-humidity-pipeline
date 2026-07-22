from dataclasses import dataclass, field

import pandas as pd


@dataclass
class CyclingDetection:
    cycling: bool
    swing_count: int
    pivot_times: list = field(default_factory=list)


def detect_cycling(
    temps: pd.Series,
    *,
    min_amplitude_c: float = 0.8,
    min_swings: int = 4,
    presmooth: int | None = 3,
) -> CyclingDetection:
    """温度系列からエアコンのサーモスタットサイクル(周期的な上下)を検出する。

    zigzag 法: 振幅 min_amplitude_c 以上の反転(山・谷)を数え、
    min_swings 回以上あればサイクル中と判定する。ドア開閉のような
    単発イベントは反転が 2 回で止まるため区別できる。

    presmooth はセンサーの単発外れ値を除去するためのセンター中央値の
    窓幅(サンプル数)。サイクルの山谷は複数サンプル持続するため残る。
    """
    s = temps.dropna()
    if presmooth and len(s) >= presmooth:
        s = s.rolling(presmooth, center=True).median().dropna()
    if len(s) < 3:
        return CyclingDetection(False, 0)

    pivots: list = []
    values = s.to_numpy()
    times = s.index
    min_v = max_v = values[0]
    min_t = max_t = times[0]
    direction = 0  # +1: 上昇脚, -1: 下降脚
    for t, v in zip(times[1:], values[1:]):
        if v > max_v:
            max_v, max_t = v, t
        if v < min_v:
            min_v, min_t = v, t
        if direction >= 0 and max_v - v >= min_amplitude_c:
            pivots.append(max_t)  # 山を確定して下降脚へ
            direction = -1
            min_v, min_t = v, t
        elif direction <= 0 and v - min_v >= min_amplitude_c:
            pivots.append(min_t)  # 谷を確定して上昇脚へ
            direction = 1
            max_v, max_t = v, t

    return CyclingDetection(len(pivots) >= min_swings, len(pivots), pivots)
