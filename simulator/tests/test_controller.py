import unittest

from lamp_sim.controller import LampController
from lamp_sim.model import AutoState, Command, CommandType, LampConfig, LampMode, Presence, SensorFrame


def frame(lux=100, presence=Presence.PRESENT, lux_valid=True, presence_valid=True):
    return SensorFrame(lux, lux_valid, presence, presence_valid)


def powered_controller(config=None):
    c = LampController(config or LampConfig())
    c.step(0, frame(), (Command(CommandType.POWER_ON), Command(CommandType.AUTO_MODE)))
    return c


class ControllerModeTests(unittest.TestCase):
    def test_new_controller_is_software_off(self):
        out = LampController().step(0, frame())
        self.assertFalse(out.software_powered)
        self.assertEqual(0, out.target_brightness)

    def test_automatic_decisions_and_hysteresis(self):
        c = powered_controller()
        self.assertEqual(80, c.step(1, frame(100)).target_brightness)
        self.assertEqual(0, c.step(2, frame(400)).target_brightness)
        self.assertEqual(0, c.step(3, frame(300)).target_brightness)
        self.assertEqual(50, c.step(4, frame(200)).target_brightness)
        self.assertEqual(50, c.step(5, frame(300)).target_brightness)

    def test_manual_brightness_clamps_and_ignores_sensors(self):
        c = powered_controller()
        out = c.step(1, frame(500, Presence.ABSENT), (Command(CommandType.SET_BRIGHTNESS, 5, "app"),))
        self.assertEqual(LampMode.MANUAL, out.mode)
        self.assertEqual(10, out.target_brightness)
        self.assertEqual(10, c.step(2, frame(500, Presence.ABSENT)).target_brightness)
        self.assertEqual(0, c.step(3, frame(), (Command(CommandType.SET_BRIGHTNESS, 0, "voice"),)).target_brightness)

    def test_return_to_auto_rechecks_sensors(self):
        c = powered_controller()
        c.step(1, frame(), (Command(CommandType.SET_BRIGHTNESS, 40),))
        out = c.step(2, frame(400), (Command(CommandType.AUTO_MODE),))
        self.assertEqual(LampMode.AUTO, out.mode)
        self.assertEqual(0, out.target_brightness)

    def test_time_cannot_go_backwards(self):
        c = LampController()
        c.step(5, frame())
        with self.assertRaises(ValueError):
            c.step(4, frame())


class VacancyAndDimmingTests(unittest.TestCase):
    def test_vacancy_delay_then_shutdown_and_return_cancels(self):
        c = powered_controller(LampConfig(fade_rate_per_s=100))
        c.step(1, frame())
        delayed = c.step(10, frame(presence=Presence.ABSENT))
        self.assertEqual(AutoState.VACANCY_DELAY, delayed.auto_state)
        self.assertEqual(10, delayed.target_brightness)
        self.assertEqual(119.9, c.step(129.9, frame(presence=Presence.ABSENT)).vacancy_elapsed_s)
        self.assertEqual(0, c.step(130, frame(presence=Presence.ABSENT)).target_brightness)

        c2 = powered_controller()
        c2.step(10, frame(presence=Presence.ABSENT))
        returned = c2.step(70, frame(presence=Presence.PRESENT))
        self.assertEqual(AutoState.AUTO_LIGHTING, returned.auto_state)
        self.assertIsNone(returned.vacancy_elapsed_s)
        self.assertEqual(80, returned.target_brightness)

    def test_dimmer_uses_elapsed_virtual_time(self):
        c = powered_controller()
        self.assertEqual(20, c.step(1, frame()).actual_brightness)
        self.assertEqual(30, c.step(1.5, frame()).actual_brightness)


class FaultTests(unittest.TestCase):
    def test_bh1750_fault_freezes_then_recovers(self):
        c = powered_controller(LampConfig(fade_rate_per_s=100))
        c.step(1, frame(100))
        fault = c.step(2, frame(None, lux_valid=False))
        self.assertTrue(fault.bh1750_fault)
        self.assertEqual(80, fault.target_brightness)
        recovered = c.step(3, frame(400))
        self.assertFalse(recovered.bh1750_fault)
        self.assertEqual(0, recovered.target_brightness)

    def test_radar_fault_freezes_vacancy_and_requires_three_frames(self):
        c = powered_controller(LampConfig(fade_rate_per_s=100))
        c.step(1, frame())
        c.step(10, frame(presence=Presence.ABSENT))
        unknown = c.step(20, frame(presence_valid=False))
        self.assertEqual(Presence.UNKNOWN, unknown.effective_presence)
        self.assertEqual(10, unknown.vacancy_elapsed_s)
        self.assertEqual(1, c.step(30, frame(presence=Presence.ABSENT)).radar_recovery_progress)
        self.assertEqual(2, c.step(40, frame(presence=Presence.ABSENT)).radar_recovery_progress)
        restored = c.step(50, frame(presence=Presence.ABSENT))
        self.assertFalse(restored.ld2410_fault)
        self.assertEqual(10, restored.vacancy_elapsed_s)

    def test_invalid_frame_resets_radar_recovery(self):
        c = powered_controller()
        c.step(1, frame(presence_valid=False))
        self.assertEqual(1, c.step(2, frame()).radar_recovery_progress)
        self.assertEqual(0, c.step(3, frame(presence_valid=False)).radar_recovery_progress)

    def test_double_fault_still_allows_manual_and_power_off(self):
        c = powered_controller()
        both = frame(None, Presence.UNKNOWN, False, False)
        out = c.step(1, both, (Command(CommandType.SET_BRIGHTNESS, 40),))
        self.assertTrue(out.bh1750_fault and out.ld2410_fault)
        self.assertEqual(40, out.target_brightness)
        self.assertFalse(c.step(2, both, (Command(CommandType.POWER_OFF),)).software_powered)


if __name__ == "__main__":
    unittest.main()
