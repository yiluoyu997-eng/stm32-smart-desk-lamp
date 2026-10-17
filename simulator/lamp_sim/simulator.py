from __future__ import annotations

from datetime import datetime, timedelta

from .controller import LampController
from .model import Command, LampOutput, SensorFrame


class LampSimulator:
    def __init__(self, controller: LampController, start_datetime: datetime,
                 initial_sensors: SensorFrame) -> None:
        self.controller = controller
        self.now_s = 0.0
        self.now_datetime = start_datetime
        self.sensors = initial_sensors

    def advance(self, seconds: float, sensors: SensorFrame | None = None,
                commands: tuple[Command, ...] = ()) -> LampOutput:
        if seconds < 0:
            raise ValueError("simulation cannot advance by negative time")
        self.now_s += seconds
        self.now_datetime += timedelta(seconds=seconds)
        if sensors is not None:
            self.sensors = sensors
        return self.controller.step(
            self.now_s, self.sensors, commands, self.now_datetime
        )
