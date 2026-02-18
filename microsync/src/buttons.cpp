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
#include "uart_comm.h"

/** D36 = PC4, D37 = PC5, D38 = PC6 on PIOC */
#define BUTTON_D36_MASK  PIO_PC4
#define BUTTON_D37_MASK  PIO_PC5
#define BUTTON_D38_MASK  PIO_PC6
#define ALL_BUTTONS_MASK (BUTTON_D36_MASK | BUTTON_D37_MASK | BUTTON_D38_MASK)

/** Debounce: SLCK / (DIV+1). DIV=655 -> ~20 ms at 32 kHz */
#define BUTTON_DEBOUNCE_DIV  655u

static volatile bool button_d36_pending = false;
static volatile bool button_d37_pending = false;
static volatile bool button_d38_pending = false;

static void button_d36_handler(uint32_t id, uint32_t mask);
static void button_d37_handler(uint32_t id, uint32_t mask);
static void button_d38_handler(uint32_t id, uint32_t mask);

void init_buttons(void)
{
	sysclk_enable_peripheral_clock(ID_PIOC);

	/* Debounce filter for all three pins */
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

void process_button_events(void)
{
	if (button_d36_pending) {
		button_d36_pending = false;
		stop_burst_func(0, 0);
		stop_sys_timer();
		std::priority_queue<Event>().swap(event_queue);
		err_led_off();
		init_pins();
		DataPacket data;
		data.arg1 = 100000;
		data.N = 30;
		data.interv_us = 800000;
		start_ALEX_acq(&data);
		start_sys_timer();
	}
	if (button_d37_pending) {
		button_d37_pending = false;
		stop_burst_func(0, 0);
		stop_sys_timer();
		std::priority_queue<Event>().swap(event_queue);
		err_led_off();
		init_pins();
		DataPacket data;
		data.arg1 = 100000;
		data.N = 30;
		start_continuous_acq(&data);
		start_sys_timer();
	}
	if (button_d38_pending) {
		button_d38_pending = false;
		stop_sys_timer();
	}

	/* Re-enable so next press can fire (no new interrupt until main has processed) */
	pio_enable_interrupt(PIOC, ALL_BUTTONS_MASK);
}
