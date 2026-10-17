import unittest
from datetime import datetime

from lamp_sim.controller import LampController
from lamp_sim.model import AlarmSchedule, Command, CommandType, LampConfig, Presence, SensorFrame
from lamp_sim.simulator import LampSimulator


class IntegratedScenarioTests(unittest.TestCase):
    def test_virtual_timeline_covers_fault_delay_shutdown_and_alarm(self):
        alarm = AlarmSchedule("demo", datetime(2026, 9, 12, 7, 5), allow_when_software_off=True)
        simulator = LampSimulator(
            LampController(LampConfig(fade_rate_per_s=100), (alarm,)),
            datetime(2026, 9, 12, 7, 0),
            SensorFrame(100, True, Presence.PRESENT, True),
        )
        simulator.advance(0, commands=(Command(CommandType.POWER_ON), Command(CommandType.AUTO_MODE)))
        simulator.advance(10, SensorFrame(100, True, Presence.ABSENT, True))
        simulator.advance(20, SensorFrame(100, True, Presence.UNKNOWN, False))
        simulator.advance(20, SensorFrame(100, True, Presence.ABSENT, True))
        simulator.advance(1, SensorFrame(100, True, Presence.ABSENT, True))
        recovered = simulator.advance(1, SensorFrame(100, True, Presence.ABSENT, True))
        self.assertFalse(recovered.ld2410_fault)
        off = simulator.advance(110, SensorFrame(100, True, Presence.ABSENT, True))
        self.assertEqual(0, off.target_brightness)
        alarm_out = simulator.advance(138)
        self.assertTrue(alarm_out.alarm_active)
        restored = simulator.advance(1, commands=(Command(CommandType.BUTTON_PRESS),))
        self.assertFalse(restored.alarm_active)
        self.assertEqual(0, restored.target_brightness)


if __name__ == "__main__":
    unittest.main()
