from datetime import datetime, timedelta

from automation.rules import decide

_NOW = datetime(2026, 7, 20, 15, 0, 0)


def _decide(**kwargs):
    defaults = dict(
        ac_cycling=True,
        last_motion=_NOW - timedelta(hours=13),
        last_action=None,
        now=_NOW,
        no_motion_hours=12.0,
        cooldown_hours=3.0,
    )
    defaults.update(kwargs)
    return decide(**defaults)


class TestDecide:
    def test_turns_off_when_cycling_and_long_absence(self):
        assert _decide().action == "turn_off"

    def test_no_action_when_not_cycling(self):
        assert _decide(ac_cycling=False).action == "none"

    def test_no_action_when_motion_is_recent(self):
        assert _decide(last_motion=_NOW - timedelta(hours=1)).action == "none"

    def test_no_action_when_no_motion_data(self):
        # 人感センサー未設置/未検知データなしの場合は安全側(何もしない)
        assert _decide(last_motion=None).action == "none"

    def test_no_action_during_cooldown(self):
        assert _decide(last_action=_NOW - timedelta(hours=1)).action == "none"

    def test_acts_again_after_cooldown(self):
        assert _decide(last_action=_NOW - timedelta(hours=4)).action == "turn_off"

    def test_exact_threshold_triggers(self):
        assert _decide(last_motion=_NOW - timedelta(hours=12)).action == "turn_off"

    def test_reason_is_populated(self):
        assert _decide(ac_cycling=False).reason
