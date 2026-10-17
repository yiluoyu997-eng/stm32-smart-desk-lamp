import unittest
from datetime import datetime, time

from lamp_sim.alarm import AlarmEngine, breathing_brightness
from lamp_sim.controller import LampController
from lamp_sim.model import AlarmSchedule, Command, CommandType, LampConfig, LampMode, Presence, SensorFrame


FRAME = SensorFrame(100, True, Presence.PRESENT, True)


class AlarmEngineTests(unittest.TestCase):
    def test_one_shot_and_daily_alarm_only_trigger_once(self):
        once = AlarmSchedule("once", datetime(2026, 9, 12, 7, 0))
        daily = AlarmSchedule("daily", time(7, 30), daily=True)
        engine = AlarmEngine((once, daily))
        self.assertEqual(["once"], [a.alarm_id for a in engine.due(datetime(2026, 9, 12, 7, 0), True)])
        self.assertEqual([], engine.due(datetime(2026, 9, 12, 7, 0, 30), True))
        self.assertEqual(["daily"], [a.alarm_id for a in engine.due(datetime(2026, 9, 12, 7, 30), True)])
        self.assertEqual([], engine.due(datetime(2026, 9, 12, 7, 30, 30), True))
        self.assertEqual(["daily"], [a.alarm_id for a in engine.due(datetime(2026, 9, 13, 7, 30), True)])

    def test_software_off_policy(self):
        denied = AlarmSchedule("denied", datetime(2026, 9, 12, 8), allow_when_software_off=False)
        allowed = AlarmSchedule("allowed", datetime(2026, 9, 12, 8), allow_when_software_off=True)
        self.assertEqual([], AlarmEngine((denied,)).due(datetime(2026, 9, 12, 8), False))
        self.assertEqual(["allowed"], [a.alarm_id for a in AlarmEngine((allowed,)).due(datetime(2026, 9, 12, 8), False)])

    def test_breathing_is_deterministic(self):
        self.assertEqual(10, breathing_brightness(0, 10, 60, 2))
        self.assertEqual(60, breathing_brightness(1, 10, 60, 2))
        self.assertEqual(10, breathing_brightness(2, 10, 60, 2))


class ControllerAlarmTests(unittest.TestCase):
    def test_button_acknowledges_without_executing_normal_action(self):
        alarm = AlarmSchedule("wake", datetime(2026, 9, 12, 7), allow_when_software_off=True)
        c = LampController(LampConfig(fade_rate_per_s=100), (alarm,))
        active = c.step(0, FRAME, now_datetime=datetime(2026, 9, 12, 7))
        self.assertTrue(active.alarm_active)
        stopped = c.step(1, FRAME, (Command(CommandType.BUTTON_PRESS),), datetime(2026, 9, 12, 7, 0, 1))
        self.assertFalse(stopped.alarm_active)
        self.assertFalse(stopped.software_powered)

    def test_alarm_restores_auto_and_rechecks_environment(self):
        alarm = AlarmSchedule("wake", datetime(2026, 9, 12, 7))
        c = LampController(LampConfig(fade_rate_per_s=100), (alarm,))
        c.step(0, FRAME, (Command(CommandType.POWER_ON), Command(CommandType.AUTO_MODE)), datetime(2026, 9, 12, 6, 59))
        self.assertTrue(c.step(60, FRAME, now_datetime=datetime(2026, 9, 12, 7)).alarm_active)
        bright = SensorFrame(500, True, Presence.PRESENT, True)
        restored = c.step(61, bright, (Command(CommandType.BUTTON_PRESS),), datetime(2026, 9, 12, 7, 0, 1))
        self.assertEqual(LampMode.AUTO, restored.mode)
        self.assertEqual(0, restored.target_brightness)


if __name__ == "__main__":
    unittest.main()
