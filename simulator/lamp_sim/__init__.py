"""基于虚拟时间的智能台灯控制逻辑模拟。"""

from .controller import LampController
from .model import (
    AlarmSchedule, AutoState, Command, CommandType, LampConfig, LampMode,
    LampOutput, Presence, SensorFrame,
)
from .simulator import LampSimulator

__all__ = [
    "AlarmSchedule", "AutoState", "Command", "CommandType", "LampConfig",
    "LampController", "LampMode", "LampOutput", "LampSimulator", "Presence",
    "SensorFrame",
]
