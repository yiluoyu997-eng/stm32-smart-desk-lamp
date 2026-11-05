# NUCLEO-F411RE 固件工作区

## V1范围

- 主控：NUCLEO-F411RE；
- 自动闭环：BH1750照度 + LD2410C人员存在 + 双路PWM灯带；
- 本地交互：EC11、SSD1306 OLED、SHT30、DS3231、蜂鸣器；
- 蓝牙：暂缓，保留PC6/PC7接口；
- 语音：暂缓，保留PA2/PA3接口；
- 首版采用裸机协作式调度，不先上FreeRTOS。

`Core/` 是不依赖STM32 HAL的控制核心，可由Arm Compiler 6单独做语法和目标代码编译。
`config/nucleo_f411re_pins.h` 冻结第一版引脚。`STM32F411RE/MDK-ARM/Project.uvprojx` 是可打开、可构建的Keil工程骨架。

## 准备与构建

在仓库根目录运行：

```powershell
.\firmware\tools\setup_stm32cube.ps1
.\firmware\tools\build_core_armclang.ps1
.\firmware\tools\build_keil.ps1
```

依赖脚本只从ST官方STM32CubeF4仓库和Keil官方设备包下载文件。生成物位于`firmware/STM32F411RE/build/`，不提交到Git。

## 外设配置合同

| 功能 | 外设/引脚 | 初始设置 |
| --- | --- | --- |
| 调试串口 | USART2 PA2/PA3 | 115200 8N1，蓝牙/语音未启用时保留给VCP |
| LD2410C | USART1 PA9/PA10 | 按模块默认波特率核对后填写 |
| I²C总线 | I2C1 PB8/PB9 | 100 kHz起步；BH1750/OLED/SHT30/DS3231共线 |
| 暖光PWM | TIM1_CH1 PA8 | 20 kHz起步，实物检查模块和频闪后确认 |
| 冷光PWM | TIM4_CH1 PB6 | 20 kHz起步，实物检查模块和频闪后确认 |
| EC11 | PA6/PA7/PB0 | GPIO输入，上拉，软件消抖 |
| RTC中断 | PB1 | 外部中断，下降沿；实物确认SQW电平 |
| 蜂鸣器 | PC0 | GPIO输出；有源蜂鸣器只做开关控制 |

## 当前验证边界

已经完成：控制核心源码、引脚合同、Arm Cortex-M4目标编译、Keil F411RE工程构建、电脑端23项行为测试。

仍需开发板：HAL外设初始化、下载运行、传感器真实通信、PWM波形、灯带电流/温升和整机联调。任何这些项目在实测前都保持“待验证”。
