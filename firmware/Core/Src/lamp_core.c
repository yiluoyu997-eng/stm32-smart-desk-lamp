#include "lamp_core.h"

#include <stddef.h>

static uint16_t clamp_per_mille(uint16_t value)
{
    return value > 1000U ? 1000U : value;
}

static uint16_t mapped_brightness(const LampController *controller, uint16_t lux)
{
    uint16_t value = lux < 100U ? 1000U : (lux < 180U ? 800U : 500U);
    return value < controller->config.bmin_per_mille
               ? controller->config.bmin_per_mille
               : value;
}

static void update_light_classification(LampController *controller, uint16_t lux)
{
    if (!controller->darkness_initialized) {
        controller->is_dark = lux < controller->config.bright_threshold_lux;
        controller->darkness_initialized = true;
    } else if (controller->is_dark && lux >= controller->config.bright_threshold_lux) {
        controller->is_dark = false;
    } else if (!controller->is_dark && lux <= controller->config.dark_threshold_lux) {
        controller->is_dark = true;
    }
}

static uint32_t vacancy_elapsed(const LampController *controller, uint32_t now_ms)
{
    if (!controller->snapshot.vacancy_timer_active) {
        return 0U;
    }
    if (controller->snapshot.ld2410_fault) {
        return controller->frozen_vacancy_elapsed_ms;
    }
    return now_ms - controller->vacancy_start_ms;
}

static void update_faults(LampController *controller,
                          const LampInputs *inputs,
                          uint32_t now_ms)
{
    if (!inputs->lux_valid) {
        if (!controller->snapshot.bh1750_fault) {
            controller->bh1750_frozen_per_mille = controller->snapshot.actual_per_mille;
        }
        controller->snapshot.bh1750_fault = true;
    } else {
        controller->snapshot.bh1750_fault = false;
    }

    if (!inputs->presence_valid) {
        if (!controller->snapshot.ld2410_fault) {
            controller->frozen_vacancy_elapsed_ms = vacancy_elapsed(controller, now_ms);
        }
        controller->snapshot.ld2410_fault = true;
        controller->snapshot.radar_recovery_progress = 0U;
    } else if (controller->snapshot.ld2410_fault) {
        controller->snapshot.radar_recovery_progress++;
        if (controller->snapshot.radar_recovery_progress >=
            controller->config.radar_recovery_frames) {
            if (controller->snapshot.vacancy_timer_active) {
                controller->vacancy_start_ms = now_ms - controller->frozen_vacancy_elapsed_ms;
            }
            controller->snapshot.ld2410_fault = false;
            controller->snapshot.radar_recovery_progress = 0U;
        }
    }
}

static void select_target(LampController *controller,
                          const LampInputs *inputs,
                          uint32_t now_ms)
{
    LampSnapshot *snapshot = &controller->snapshot;

    if (!snapshot->software_powered) {
        snapshot->target_per_mille = 0U;
        snapshot->auto_state = LAMP_AUTO_OFF;
        snapshot->vacancy_timer_active = false;
        return;
    }
    if (snapshot->mode == LAMP_MODE_MANUAL) {
        return;
    }
    if (snapshot->bh1750_fault) {
        snapshot->target_per_mille = controller->bh1750_frozen_per_mille;
        return;
    }

    update_light_classification(controller, inputs->lux);
    if (!controller->is_dark) {
        snapshot->target_per_mille = 0U;
        snapshot->auto_state = LAMP_AUTO_OFF;
        snapshot->vacancy_timer_active = false;
        return;
    }
    if (snapshot->effective_presence == LAMP_PRESENCE_UNKNOWN) {
        return;
    }
    if (snapshot->effective_presence == LAMP_PRESENCE_PRESENT) {
        snapshot->target_per_mille = mapped_brightness(controller, inputs->lux);
        snapshot->auto_state = LAMP_AUTO_LIGHTING;
        snapshot->vacancy_timer_active = false;
        return;
    }
    if (snapshot->target_per_mille == 0U && snapshot->actual_per_mille == 0U) {
        snapshot->auto_state = LAMP_AUTO_OFF;
        return;
    }
    if (!snapshot->vacancy_timer_active) {
        snapshot->vacancy_timer_active = true;
        controller->vacancy_start_ms = now_ms;
    }
    snapshot->auto_state = LAMP_AUTO_VACANCY_DELAY;
    snapshot->target_per_mille =
        vacancy_elapsed(controller, now_ms) >= controller->config.vacancy_delay_ms
            ? 0U
            : controller->config.standby_per_mille;
}

static void update_ramp(LampController *controller, uint32_t elapsed_ms)
{
    LampSnapshot *snapshot = &controller->snapshot;
    uint32_t step = ((uint32_t)controller->config.fade_per_mille_per_s * elapsed_ms) / 1000U;

    if (step == 0U || snapshot->actual_per_mille == snapshot->target_per_mille) {
        return;
    }
    if (snapshot->actual_per_mille < snapshot->target_per_mille) {
        uint32_t next = (uint32_t)snapshot->actual_per_mille + step;
        snapshot->actual_per_mille = next > snapshot->target_per_mille
                                         ? snapshot->target_per_mille
                                         : (uint16_t)next;
    } else {
        snapshot->actual_per_mille = step >= snapshot->actual_per_mille - snapshot->target_per_mille
                                         ? snapshot->target_per_mille
                                         : (uint16_t)(snapshot->actual_per_mille - step);
    }
}

LampConfig LampConfig_Default(void)
{
    LampConfig config = {
        100U, 100U, 250U, 350U, 120000U, 200U, 3U
    };
    return config;
}

bool LampConfig_IsValid(const LampConfig *config)
{
    return config != NULL &&
           config->bmin_per_mille > 0U && config->bmin_per_mille <= 1000U &&
           config->standby_per_mille >= config->bmin_per_mille &&
           config->standby_per_mille <= 1000U &&
           config->dark_threshold_lux < config->bright_threshold_lux &&
           config->fade_per_mille_per_s > 0U &&
           config->radar_recovery_frames > 0U;
}

void LampController_Init(LampController *controller, const LampConfig *config)
{
    LampConfig selected = LampConfig_IsValid(config) ? *config : LampConfig_Default();
    *controller = (LampController){0};
    controller->config = selected;
    controller->snapshot.mode = LAMP_MODE_AUTO;
    controller->snapshot.auto_state = LAMP_AUTO_OFF;
    controller->snapshot.effective_presence = LAMP_PRESENCE_UNKNOWN;
    controller->snapshot.cct_per_mille = 500U;
}

bool LampController_HandleCommand(LampController *controller, const LampCommand *command)
{
    if (controller == NULL || command == NULL) {
        return false;
    }
    switch (command->type) {
    case LAMP_CMD_POWER_ON:
        controller->snapshot.software_powered = true;
        return true;
    case LAMP_CMD_POWER_OFF:
        controller->snapshot.software_powered = false;
        controller->snapshot.target_per_mille = 0U;
        return true;
    case LAMP_CMD_AUTO_MODE:
        controller->snapshot.mode = LAMP_MODE_AUTO;
        controller->snapshot.vacancy_timer_active = false;
        return true;
    case LAMP_CMD_SET_BRIGHTNESS:
        if (command->value_per_mille > 1000U) {
            return false;
        }
        controller->snapshot.software_powered = true;
        controller->snapshot.mode = LAMP_MODE_MANUAL;
        controller->snapshot.target_per_mille = command->value_per_mille == 0U
            ? 0U
            : (command->value_per_mille < controller->config.bmin_per_mille
                   ? controller->config.bmin_per_mille
                   : command->value_per_mille);
        return true;
    case LAMP_CMD_NONE:
    default:
        return false;
    }
}

LampSnapshot LampController_Update(LampController *controller,
                                   const LampInputs *inputs,
                                   uint32_t now_ms)
{
    uint32_t elapsed_ms = controller->time_initialized
                              ? now_ms - controller->last_update_ms
                              : 0U;
    controller->time_initialized = true;
    update_faults(controller, inputs, now_ms);
    controller->snapshot.effective_presence =
        controller->snapshot.ld2410_fault || !inputs->presence_valid
            ? LAMP_PRESENCE_UNKNOWN
            : inputs->presence;
    select_target(controller, inputs, now_ms);
    update_ramp(controller, elapsed_ms);
    controller->snapshot.vacancy_elapsed_ms = vacancy_elapsed(controller, now_ms);
    controller->last_update_ms = now_ms;
    return controller->snapshot;
}

LampChannelOutput LampCore_MixChannels(uint16_t brightness_per_mille,
                                       uint16_t cct_per_mille)
{
    uint32_t brightness = clamp_per_mille(brightness_per_mille);
    uint32_t cct = clamp_per_mille(cct_per_mille);
    LampChannelOutput output = {
        (uint16_t)((brightness * (1000U - cct)) / 1000U),
        (uint16_t)((brightness * cct) / 1000U)
    };
    return output;
}
