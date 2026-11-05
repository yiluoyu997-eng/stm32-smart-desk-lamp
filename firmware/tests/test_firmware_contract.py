from __future__ import annotations

import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
FIRMWARE = ROOT / "firmware"


class FirmwareContractTests(unittest.TestCase):
    def test_core_files_exist(self) -> None:
        required = (
            FIRMWARE / "Core" / "Inc" / "lamp_core.h",
            FIRMWARE / "Core" / "Src" / "lamp_core.c",
            FIRMWARE / "config" / "nucleo_f411re_pins.h",
            FIRMWARE / "STM32F411RE" / "MDK-ARM" / "Project.uvprojx",
            FIRMWARE / "README.md",
        )
        self.assertEqual([], [str(path) for path in required if not path.is_file()])

    def test_frozen_pin_contract(self) -> None:
        text = (FIRMWARE / "config" / "nucleo_f411re_pins.h").read_text(encoding="utf-8")
        expected = {
            "LAMP_PIN_LD2410_TX": "PA9",
            "LAMP_PIN_LD2410_RX": "PA10",
            "LAMP_PIN_I2C_SCL": "PB8",
            "LAMP_PIN_I2C_SDA": "PB9",
            "LAMP_PIN_PWM_WARM": "PA8",
            "LAMP_PIN_PWM_COOL": "PB6",
            "LAMP_PIN_ENCODER_A": "PA6",
            "LAMP_PIN_ENCODER_B": "PA7",
            "LAMP_PIN_ENCODER_SW": "PB0",
            "LAMP_PIN_RTC_INT": "PB1",
            "LAMP_PIN_BUZZER": "PC0",
        }
        for name, value in expected.items():
            self.assertRegex(text, rf"#define\s+{name}\s+{value}\b")

    def test_core_has_no_stm32_or_hal_dependency(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                FIRMWARE / "Core" / "Inc" / "lamp_core.h",
                FIRMWARE / "Core" / "Src" / "lamp_core.c",
            )
        )
        self.assertIsNone(re.search(r"stm32|HAL_", combined, flags=re.IGNORECASE))

    def test_first_release_explicitly_defers_voice_and_bluetooth(self) -> None:
        text = (FIRMWARE / "README.md").read_text(encoding="utf-8")
        self.assertIn("蓝牙：暂缓", text)
        self.assertIn("语音：暂缓", text)

    def test_keil_project_targets_f411_and_builds_hex(self) -> None:
        text = (FIRMWARE / "STM32F411RE" / "MDK-ARM" / "Project.uvprojx").read_text(
            encoding="utf-8"
        )
        self.assertIn("<Device>STM32F411RETx</Device>", text)
        self.assertIn("<PackID>Keil.STM32F4xx_DFP.3.1.1</PackID>", text)
        self.assertIn("<CreateHexFile>1</CreateHexFile>", text)
        self.assertIn("<FileName>lamp_core.c</FileName>", text)


if __name__ == "__main__":
    unittest.main()
