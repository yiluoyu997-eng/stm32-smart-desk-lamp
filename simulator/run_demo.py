from datetime import datetime

from lamp_sim import (
    AlarmSchedule, Command, CommandType, LampConfig, LampController,
    LampSimulator, Presence, SensorFrame,
)


def sensor(lux=100, presence=Presence.PRESENT, lux_ok=True, radar_ok=True):
    return SensorFrame(lux, lux_ok, presence, radar_ok)


def show(label, output):
    faults = ",".join(name for name, active in (
        ("BH1750", output.bh1750_fault), ("LD2410", output.ld2410_fault)
    ) if active) or "无"
    print(
        f"{output.now_s:>6.0f}s | {label:<14} | {output.mode.value:<6} | "
        f"{output.auto_state.value:<15} | 人员={output.effective_presence.value:<7} | "
        f"目标={output.target_brightness:>5.1f}% | 实际={output.actual_brightness:>5.1f}% | "
        f"故障={faults:<14} | 闹钟={'是' if output.alarm_active else '否'}"
    )


def main():
    alarm = AlarmSchedule(
        "demo-alarm", datetime(2026, 9, 12, 7, 5),
        allow_when_software_off=True,
    )
    sim = LampSimulator(
        LampController(LampConfig(fade_rate_per_s=20), (alarm,)),
        datetime(2026, 9, 12, 7, 0), sensor(),
    )
    show("暗处有人，自动启动", sim.advance(
        0, commands=(Command(CommandType.POWER_ON), Command(CommandType.AUTO_MODE))
    ))
    show("渐亮", sim.advance(4))
    show("人员离开，进入待机", sim.advance(6, sensor(presence=Presence.ABSENT)))
    show("雷达通信故障", sim.advance(20, sensor(presence=Presence.UNKNOWN, radar_ok=False)))
    show("恢复样本 1/3", sim.advance(20, sensor(presence=Presence.ABSENT)))
    show("恢复样本 2/3", sim.advance(1, sensor(presence=Presence.ABSENT)))
    show("恢复样本 3/3", sim.advance(1, sensor(presence=Presence.ABSENT)))
    show("有效无人累计满 120 秒", sim.advance(110, sensor(presence=Presence.ABSENT)))
    show("渐灭完成", sim.advance(5))
    show("闹钟到点，呼吸提醒", sim.advance(133))
    show("按键停止并恢复自动状态", sim.advance(
        1, commands=(Command(CommandType.BUTTON_PRESS),)
    ))


if __name__ == "__main__":
    main()
