#ifndef NUCLEO_F411RE_PINS_H
#define NUCLEO_F411RE_PINS_H

/* Frozen V1 logical pin contract. These tokens are documentation identifiers;
 * the generated HAL adapter will map them to GPIO ports and alternate functions. */
#define LAMP_PIN_LD2410_TX PA9
#define LAMP_PIN_LD2410_RX PA10
#define LAMP_PIN_I2C_SCL PB8
#define LAMP_PIN_I2C_SDA PB9
#define LAMP_PIN_PWM_WARM PA8
#define LAMP_PIN_PWM_COOL PB6
#define LAMP_PIN_ENCODER_A PA6
#define LAMP_PIN_ENCODER_B PA7
#define LAMP_PIN_ENCODER_SW PB0
#define LAMP_PIN_RTC_INT PB1
#define LAMP_PIN_BUZZER PC0

/* Reserved for later releases; not enabled in V1. */
#define LAMP_PIN_BLE_TX PC6
#define LAMP_PIN_BLE_RX PC7
#define LAMP_PIN_VOICE_TX PA2
#define LAMP_PIN_VOICE_RX PA3

#endif
