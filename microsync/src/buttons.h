/**
 * @file buttons.h
 * @brief Button input on D36–D38 and demo settings.
 */

#pragma once

#include <stdint.h>

/** Acquisition mode for demo: continuous, ALEX, or stroboscopic */
typedef enum {
	DEMO_ACQ_CONTINUOUS = 0,
	DEMO_ACQ_ALEX,
	DEMO_ACQ_STROBOSCOPIC
} DemoAcqMode;

/** Globally visible demo settings; updated by button presses. */
typedef struct {
	DemoAcqMode acquisition_mode;
	uint32_t    exposure_ms;      /**< 25, 100, 250, or 1000 */
	uint32_t    selected_lasers;  /**< 0b0000, 0b0100, 0b0110, or 0b1111 */
} DemoSettings;

extern DemoSettings demoSettings;

void init_buttons(void);

/** Call from main loop to process any pending button press; re-enables interrupts after handling. */
void process_button_events(void);
