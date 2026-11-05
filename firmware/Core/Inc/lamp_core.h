#ifndef LAMP_CORE_H
#define LAMP_CORE_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    LAMP_MODE_AUTO = 0,
    LAMP_MODE_MANUAL
} LampMode;

typedef enum {
    LAMP_AUTO_OFF = 0,
    LAMP_AUTO_LIGHTING,
    LAMP_AUTO_VACANCY_DELAY
} LampAutoState;

typedef enum {
    LAMP_PRESENCE_UNKNOWN = 0,
    LAMP_PRESENCE_PRESENT,
    LAMP_PRESENCE_ABSENT
} LampPresence;

typedef enum {
    LAMP_CMD_NONE = 0,
    LAMP_CMD_POWER_ON,
    LAMP_CMD_POWER_OFF,
    LAMP_CMD_AUTO_MODE,
    LAMP_CMD_SET_BRIGHTNESS
} LampCommandType;

typedef struct {
    uint16_t bmin_per_mille;
    uint16_t standby_per_mille;
    uint16_t dark_threshold_lux;
    uint16_t bright_threshold_lux;
    uint32_t vacancy_delay_ms;
    uint16_t fade_per_mille_per_s;
    uint8_t radar_recovery_frames;
} LampConfig;

typedef struct {
    uint16_t lux;
    bool lux_valid;
    LampPresence presence;
    bool presence_valid;
} LampInputs;

typedef struct {
    LampCommandType type;
    uint16_t value_per_mille;
} LampCommand;

typedef struct {
    LampMode mode;
    LampAutoState auto_state;
    LampPresence effective_presence;
    bool software_powered;
    bool bh1750_fault;
    bool ld2410_fault;
    uint8_t radar_recovery_progress;
    uint16_t target_per_mille;
    uint16_t actual_per_mille;
    uint16_t cct_per_mille;
    uint32_t vacancy_elapsed_ms;
    bool vacancy_timer_active;
} LampSnapshot;

typedef struct {
    LampConfig config;
    LampSnapshot snapshot;
    bool time_initialized;
    bool darkness_initialized;
    bool is_dark;
    uint32_t last_update_ms;
    uint32_t vacancy_start_ms;
    uint32_t frozen_vacancy_elapsed_ms;
    uint16_t bh1750_frozen_per_mille;
} LampController;

typedef struct {
    uint16_t warm_per_mille;
    uint16_t cool_per_mille;
} LampChannelOutput;

LampConfig LampConfig_Default(void);
bool LampConfig_IsValid(const LampConfig *config);
void LampController_Init(LampController *controller, const LampConfig *config);
bool LampController_HandleCommand(LampController *controller, const LampCommand *command);
LampSnapshot LampController_Update(LampController *controller,
                                   const LampInputs *inputs,
                                   uint32_t now_ms);
LampChannelOutput LampCore_MixChannels(uint16_t brightness_per_mille,
                                       uint16_t cct_per_mille);

#endif
