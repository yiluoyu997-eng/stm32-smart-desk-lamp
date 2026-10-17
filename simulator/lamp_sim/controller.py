from __future__ import annotations

from datetime import datetime

from .alarm import AlarmEngine, breathing_brightness
from .dimmer import step_brightness
from .model import (
    AlarmSchedule, AutoState, Command, CommandType, LampConfig, LampMode,
    LampOutput, Presence, SensorFrame,
)


class LampController:
    def __init__(self, config: LampConfig | None = None,
                 alarms: tuple[AlarmSchedule, ...] = ()) -> None:
        self.config = config or LampConfig()
        self.mode = LampMode.AUTO
        self.software_powered = False
        self.auto_state = AutoState.OFF
        self.target = 0.0
        self.actual = 0.0
        self._last_now: float | None = None
        self._is_dark: bool | None = None
        self._vacancy_start: float | None = None
        self._frozen_vacancy_elapsed: float | None = None
        self._bh_fault = False
        self._bh_frozen = 0.0
        self._radar_fault = False
        self._radar_recovery = 0
        self._radar_fault_start: float | None = None
        self._last_effective_presence = Presence.UNKNOWN
        self._alarm_engine = AlarmEngine(alarms)
        self._alarm_active = False
        self._alarm_start_s: float | None = None
        self._alarm_saved: tuple[bool, LampMode] | None = None

    def step(self, now_s: float, sensors: SensorFrame,
             commands: tuple[Command, ...] = (),
             now_datetime: datetime | None = None) -> LampOutput:
        if self._last_now is not None and now_s < self._last_now:
            raise ValueError("simulation time cannot go backwards")
        elapsed = 0.0 if self._last_now is None else now_s - self._last_now
        self._update_faults(now_s, sensors)

        if now_datetime is not None and not self._alarm_active:
            if self._alarm_engine.due(now_datetime, self.software_powered):
                self._alarm_saved = (self.software_powered, self.mode)
                self._alarm_active = True
                self._alarm_start_s = now_s

        acknowledged = self._alarm_active and any(c.kind == CommandType.BUTTON_PRESS for c in commands)
        timed_out = (self._alarm_active and self._alarm_start_s is not None and
                     now_s - self._alarm_start_s >= self.config.alarm_timeout_s)
        if acknowledged or timed_out:
            self._alarm_active = False
            if self._alarm_saved is not None:
                self.software_powered, self.mode = self._alarm_saved
            self._alarm_saved = None
            self._alarm_start_s = None
            commands = tuple(c for c in commands if c.kind != CommandType.BUTTON_PRESS)
        elif not self._alarm_active:
            self._handle_commands(commands)

        effective_presence = self._effective_presence(sensors)
        if self._alarm_active:
            alarm_elapsed = now_s - (self._alarm_start_s or now_s)
            self.target = breathing_brightness(
                alarm_elapsed, self.config.bmin, 60.0, self.config.alarm_breath_period_s
            )
        else:
            self._select_normal_target(now_s, sensors, effective_presence)

        self.actual = step_brightness(
            self.actual, self.target, elapsed, self.config.fade_rate_per_s
        )
        self._last_now = now_s
        vacancy_elapsed = self._vacancy_elapsed(now_s)
        return LampOutput(
            now_s=now_s, mode=self.mode, software_powered=self.software_powered,
            auto_state=self.auto_state, effective_presence=effective_presence,
            target_brightness=self.target, actual_brightness=self.actual,
            vacancy_elapsed_s=vacancy_elapsed, bh1750_fault=self._bh_fault,
            ld2410_fault=self._radar_fault, radar_recovery_progress=self._radar_recovery,
            alarm_active=self._alarm_active, alarm_visual_alert=self._alarm_active,
        )

    def _handle_commands(self, commands: tuple[Command, ...]) -> None:
        for command in commands:
            if command.kind == CommandType.POWER_OFF:
                self.software_powered = False
            elif command.kind == CommandType.POWER_ON:
                self.software_powered = True
            elif command.kind == CommandType.AUTO_MODE:
                self.mode = LampMode.AUTO
            elif command.kind in (CommandType.SET_BRIGHTNESS, CommandType.SET_COLOR_TEMPERATURE):
                self.software_powered = True
                self.mode = LampMode.MANUAL
                if command.kind == CommandType.SET_BRIGHTNESS:
                    if command.value is None or not 0 <= command.value <= 100:
                        raise ValueError("manual brightness must be within 0..100")
                    self.target = 0.0 if command.value == 0 else max(self.config.bmin, float(command.value))

    def _update_faults(self, now_s: float, sensors: SensorFrame) -> None:
        if not sensors.lux_valid:
            if not self._bh_fault:
                self._bh_frozen = self.actual
            self._bh_fault = True
        else:
            self._bh_fault = False

        if not sensors.presence_valid:
            if not self._radar_fault:
                self._radar_fault_start = now_s
                self._frozen_vacancy_elapsed = self._vacancy_elapsed(now_s)
            self._radar_fault = True
            self._radar_recovery = 0
        elif self._radar_fault:
            self._radar_recovery += 1
            if self._radar_recovery >= self.config.radar_recovery_count:
                if self._vacancy_start is not None and self._radar_fault_start is not None:
                    self._vacancy_start += now_s - self._radar_fault_start
                self._radar_fault = False
                self._radar_recovery = 0
                self._radar_fault_start = None
                self._frozen_vacancy_elapsed = None

    def _effective_presence(self, sensors: SensorFrame) -> Presence:
        if self._radar_fault or not sensors.presence_valid:
            return Presence.UNKNOWN
        self._last_effective_presence = sensors.presence
        return sensors.presence

    def _select_normal_target(self, now_s: float, sensors: SensorFrame,
                              presence: Presence) -> None:
        if not self.software_powered:
            self.target = 0.0
            self.auto_state = AutoState.OFF
            self._vacancy_start = None
            return
        if self.mode == LampMode.MANUAL:
            return
        if self._bh_fault:
            self.target = self._bh_frozen
            return
        assert sensors.lux is not None
        self._update_light_classification(sensors.lux)
        if not self._is_dark:
            self.target = 0.0
            self.auto_state = AutoState.OFF
            self._vacancy_start = None
            return
        if presence == Presence.UNKNOWN:
            return
        if presence == Presence.PRESENT:
            self.target = self._mapped_brightness(sensors.lux)
            self.auto_state = AutoState.AUTO_LIGHTING
            self._vacancy_start = None
            return
        if self.target <= 0 and self.actual <= 0:
            self.auto_state = AutoState.OFF
            return
        if self._vacancy_start is None:
            self._vacancy_start = now_s
        self.auto_state = AutoState.VACANCY_DELAY
        if now_s - self._vacancy_start >= self.config.vacancy_delay_s:
            self.target = 0.0
        else:
            self.target = self.config.standby_brightness

    def _update_light_classification(self, lux: float) -> None:
        if self._is_dark is None:
            self._is_dark = lux < self.config.bright_threshold_lux
        elif self._is_dark and lux >= self.config.bright_threshold_lux:
            self._is_dark = False
        elif not self._is_dark and lux <= self.config.dark_threshold_lux:
            self._is_dark = True

    def _mapped_brightness(self, lux: float) -> float:
        value = 100.0 if lux < 100 else 80.0 if lux < 180 else 50.0
        return max(self.config.bmin, value)

    def _vacancy_elapsed(self, now_s: float) -> float | None:
        if self._vacancy_start is None:
            return None
        if self._radar_fault and self._frozen_vacancy_elapsed is not None:
            return self._frozen_vacancy_elapsed
        return now_s - self._vacancy_start
