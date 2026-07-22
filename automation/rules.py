from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Decision:
    action: str  # "turn_off" | "none"
    reason: str


def decide(
    *,
    ac_cycling: bool,
    last_motion: datetime | None,
    last_action: datetime | None,
    now: datetime,
    no_motion_hours: float = 12.0,
    cooldown_hours: float = 3.0,
) -> Decision:
    """エアコン OFF を送るべきかを判定する純粋関数。

    判定材料が欠けている場合(人感データなし)は安全側 = 何もしない。
    """
    if not ac_cycling:
        return Decision("none", "温度サイクル未検出(エアコンOFFと推測)")
    if last_motion is None:
        return Decision("none", "人感センサーの検知データなし")
    absence = now - last_motion
    if absence < timedelta(hours=no_motion_hours):
        return Decision("none", f"最終人検知から {absence.total_seconds() / 3600:.1f}h(閾値 {no_motion_hours}h 未満)")
    if last_action is not None and now - last_action < timedelta(hours=cooldown_hours):
        return Decision("none", "クールダウン中(OFF送信済み)")
    return Decision(
        "turn_off",
        f"温度サイクル検出かつ最終人検知から {absence.total_seconds() / 3600:.1f}h 経過",
    )
