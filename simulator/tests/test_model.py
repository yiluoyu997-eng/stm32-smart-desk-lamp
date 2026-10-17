import unittest

from lamp_sim.model import LampConfig


class LampConfigTests(unittest.TestCase):
    def test_rejects_zero_minimum_visible_brightness(self):
        with self.assertRaises(ValueError):
            LampConfig(bmin=0)

    def test_rejects_reversed_hysteresis_thresholds(self):
        with self.assertRaises(ValueError):
            LampConfig(dark_threshold_lux=400, bright_threshold_lux=300)

    def test_accepts_explicit_software_test_defaults(self):
        config = LampConfig()
        self.assertEqual(120.0, config.vacancy_delay_s)
        self.assertGreaterEqual(config.standby_brightness, config.bmin)


if __name__ == "__main__":
    unittest.main()
