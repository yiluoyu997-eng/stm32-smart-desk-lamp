import unittest

from lamp_sim.dimmer import step_brightness


class DimmerTests(unittest.TestCase):
    def test_moves_toward_target_without_overshoot(self):
        self.assertEqual(30.0, step_brightness(10, 80, 1, 20))
        self.assertEqual(80.0, step_brightness(75, 80, 1, 20))

    def test_fade_out_can_cross_below_bmin(self):
        self.assertEqual(5.0, step_brightness(15, 0, 0.5, 20))

    def test_rejects_invalid_time_and_rate(self):
        with self.assertRaises(ValueError):
            step_brightness(20, 40, -1, 20)
        with self.assertRaises(ValueError):
            step_brightness(20, 40, 1, 0)


if __name__ == "__main__":
    unittest.main()
