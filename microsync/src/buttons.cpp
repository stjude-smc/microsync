/**
 * @file buttons.cpp
 * @brief Detection of buttons on D36–D38
 */

#include <queue>

extern "C" {
	#include "asf.h"
}

#include "buttons.h"
#include "events.h"
#include "ext_pTIRF.h"
#include "pins.h"
#include "props.h"
#include "uart_comm.h"

/** D36 = PC4, D37 = PC5, D38 = PC6 on PIOC */
#define BUTTON_D36_MASK  PIO_PC4
#define BUTTON_D37_MASK  PIO_PC5
#define BUTTON_D38_MASK  PIO_PC6
#define ALL_BUTTONS_MASK (BUTTON_D36_MASK | BUTTON_D37_MASK | BUTTON_D38_MASK)

/** Debounce: SLCK / (DIV+1). DIV=655 -> ~20 ms at 32 kHz */
#define BUTTON_DEBOUNCE_DIV  655u

/** Exposure options for D37 cycle (ms) */
static const uint32_t exposure_options[] = { 25, 100, 250, 1000 };
static const unsigned n_exposure_options = sizeof(exposure_options) / sizeof(exposure_options[0]);

/** Selected-lasers options for D38 cycle: all off, 0b0100, 0b0110, 0b1111 */
static const uint32_t lasers_options[] = { 0b0000, 0b0100, 0b0110, 0b1111 };
static const unsigned n_lasers_options = sizeof(lasers_options) / sizeof(lasers_options[0]);

DemoSettings demoSettings = { DEMO_ACQ_CONTINUOUS, 100, 0b0100 };

static volatile bool button_d36_pending = false;
static volatile bool button_d37_pending = false;
static volatile bool button_d38_pending = false;

static void button_d36_handler(uint32_t id, uint32_t mask);
static void button_d37_handler(uint32_t id, uint32_t mask);
static void button_d38_handler(uint32_t id, uint32_t mask);

static void apply_demo_settings_and_start_acq(void);

void init_buttons(void)
{
	sysclk_enable_peripheral_clock(ID_PIOC);

	PIOC->PIO_DIFSR = ALL_BUTTONS_MASK;
	PIOC->PIO_IFER  = ALL_BUTTONS_MASK;
	PIOC->PIO_SCDR  = PIO_SCDR_DIV(BUTTON_DEBOUNCE_DIV);

	pio_handler_set(PIOC, ID_PIOC, BUTTON_D36_MASK, PIO_IT_RISE_EDGE, button_d36_handler);
	pio_handler_set(PIOC, ID_PIOC, BUTTON_D37_MASK, PIO_IT_RISE_EDGE, button_d37_handler);
	pio_handler_set(PIOC, ID_PIOC, BUTTON_D38_MASK, PIO_IT_RISE_EDGE, button_d38_handler);

	pio_enable_interrupt(PIOC, ALL_BUTTONS_MASK);
	pio_handler_set_priority(PIOC, PIOC_IRQn, 5);
}

static void button_d36_handler(uint32_t id, uint32_t mask)
{
	(void)id;
	button_d36_pending = true;
	pio_disable_interrupt(PIOC, mask);
}

static void button_d37_handler(uint32_t id, uint32_t mask)
{
	(void)id;
	button_d37_pending = true;
	pio_disable_interrupt(PIOC, mask);
}

static void button_d38_handler(uint32_t id, uint32_t mask)
{
	(void)id;
	button_d38_pending = true;
	pio_disable_interrupt(PIOC, mask);
}

static void apply_demo_settings_and_start_acq(void)
{
	set_property(rw_SELECTED_LASERS, demoSettings.selected_lasers);

	DataPacket data;
	data.arg1     = demoSettings.exposure_ms * 1000U;  /* exposure in us */
	data.ts_us    = 500000U;  /* 0.5s delay */
	data.interv_us = data.arg1*6U + 10000U;
	data.N        = 10000U/demoSettings.exposure_ms;  /* run for at least 10s */

	switch (demoSettings.acquisition_mode) {
		case DEMO_ACQ_CONTINUOUS:
			start_continuous_acq(&data);
			break;
		case DEMO_ACQ_ALEX:
			start_ALEX_acq(&data);
			break;
		case DEMO_ACQ_STROBOSCOPIC:
			start_stroboscopic_acq(&data);
			break;
	}
	start_sys_timer();
}

void process_button_events(void)
{
	if (button_d36_pending) {
		button_d36_pending = false;
		stop_sys_timer();
		clear_event_queue_and_reset_pins();
		/* Cycle acquisition mode: continuous -> ALEX -> stroboscopic -> continuous */
		demoSettings.acquisition_mode = (DemoAcqMode)((demoSettings.acquisition_mode + 1) % 3);
		apply_demo_settings_and_start_acq();
	}
	if (button_d37_pending) {
		button_d37_pending = false;
		stop_sys_timer();
		clear_event_queue_and_reset_pins();
		/* Cycle lasers: 0b0000 -> 0b0100 -> 0b0110 -> 0b1111 -> 0b0000 */
		unsigned i = 0;
		while (i < n_lasers_options && lasers_options[i] != demoSettings.selected_lasers)
			i++;
		i = (i + 1) % n_lasers_options;
		demoSettings.selected_lasers = lasers_options[i];
		apply_demo_settings_and_start_acq();
	}
	if (button_d38_pending) {
		button_d38_pending = false;
		stop_sys_timer();
		clear_event_queue_and_reset_pins();
		/* Cycle exposure: 25 -> 100 -> 250 -> 1000 -> 25 ms */
		unsigned i = 0;
		while (i < n_exposure_options && exposure_options[i] != demoSettings.exposure_ms)
			i++;
		i = (i + 1) % n_exposure_options;
		demoSettings.exposure_ms = exposure_options[i];
		apply_demo_settings_and_start_acq();
	}

	pio_enable_interrupt(PIOC, ALL_BUTTONS_MASK);
}
