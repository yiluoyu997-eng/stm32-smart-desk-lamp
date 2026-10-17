from __future__ import annotations

from datetime import datetime, time

from .model import AlarmSchedule


class AlarmEngine:
    def __init__(self, schedules: tuple[AlarmSchedule, ...] = ()) -> None:
        self.schedules = schedules
        self._fired_once: set[str] = set()
        self._daily_dates: dict[str, object] = {}

    def due(self, now: datetime, software_powered: bool) -> list[AlarmSchedule]:
        result: list[AlarmSchedule] = []
        for alarm in self.schedules:
            if not alarm.enabled or (not software_powered and not alarm.allow_when_software_off):
                continue
            if alarm.daily:
                alarm_time = alarm.at if isinstance(alarm.at, time) else alarm.at.time()
                reached = now.time() >= alarm_time
                already = self._daily_dates.get(alarm.alarm_id) == now.date()
                if reached and not already:
                    self._daily_dates[alarm.alarm_id] = now.date()
                    result.append(alarm)
            else:
                if not isinstance(alarm.at, datetime):
                    raise ValueError("one-shot alarm requires datetime")
                if now >= alarm.at and alarm.alarm_id not in self._fired_once:
                    self._fired_once.add(alarm.alarm_id)
                    result.append(alarm)
        return result


def breathing_brightness(elapsed_s: float, low: float, high: float, period_s: float) -> float:
    if elapsed_s < 0 or period_s <= 0 or not 0 <= low <= high <= 100:
        raise ValueError("invalid breathing parameters")
    phase = (elapsed_s % period_s) / period_s
    scale = phase * 2 if phase <= 0.5 else (1 - phase) * 2
    return low + (high - low) * scale
