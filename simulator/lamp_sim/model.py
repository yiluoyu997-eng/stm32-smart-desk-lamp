from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Optional


class LampMode(Enum):
    AUTO = "auto"
    MANUAL = "manual"


class AutoState(Enum):
    OFF = "off"
    AUTO_LIGHTING = "auto_lighting"
    VACANCY_DELAY = "vacancy_delay"


class Presence(Enum):
    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class CommandType(Enum):
    POWER_ON = "power_on"
    POWER_OFF = "power_off"
    AUTO_MODE = "auto_mode"
    SET_BRIGHTNESS = "set_brightness"
    SET_COLOR_TEMPERATURE = "set_color_temperature"
    BUTTON_PRESS = "button_press"


@dataclass(frozen=True)
class Command:
    kind: CommandType
    value: Optional[float] = None
    source: str = "button"


@dataclass(frozen=True)
class AlarmSchedule:
    alarm_id: str
    at: datetime | time
    daily: bool = False
    allow_when_software_off: bool = False
    enabled: bool = True


@dataclass(frozen=True)
class LampConfig:
    bmin: float = 10.0
    dark_threshold_lux: float = 250.0
    bright_threshold_lux: float = 350.0
    standby_brightness: float = 10.0
    vacancy_delay_s: float = 120.0
    fade_rate_per_s: float = 20.0
    radar_recovery_count: int = 3
    alarm_breath_period_s: float = 2.0
    alarm_timeout_s: float = 60.0

    def __post_init__(self) -> None:
        brightnesses = (self.bmin, self.standby_brightness)
        if not 0 < self.bmin <= 100 or any(not 0 <= x <= 100 for x in brightnesses):
            raise ValueError("brightness values must be within 0..100 and bmin > 0")
        if self.standby_brightness < self.bmin:
            raise ValueError("standby brightness must be at least bmin")
        if not 0 <= self.dark_threshold_lux < self.bright_threshold_lux:
            raise ValueError("dark threshold must be below bright threshold")
        if self.vacancy_delay_s < 0 or self.fade_rate_per_s <= 0:
            raise ValueError("delay must be nonnegative and fade rate positive")
        if self.radar_recovery_count <= 0:
            raise ValueError("radar recovery count must be positive")
        if self.alarm_breath_period_s <= 0 or self.alarm_timeout_s <= 0:
            raise ValueError("alarm timing must be positive")


@dataclass(frozen=True)
class SensorFrame:
    lux: Optional[float]
    lux_valid: bool
    presence: Presence
    presence_valid: bool


@dataclass(frozen=True)
class LampOutput:
    now_s: float
    mode: LampMode
    software_powered: bool
    auto_state: AutoState
    effective_presence: Presence
    target_brightness: float
    actual_brightness: float
    vacancy_elapsed_s: Optional[float]
    bh1750_fault: bool
    ld2410_fault: bool
    radar_recovery_progress: int
    alarm_active: bool = False
    alarm_visual_alert: bool = False
