/**
 * @file buttons.cpp
 * @brief Button on D38 (PC6): debounce filter, rising-edge interrupt, calls stop_sys_timer.
 */

extern "C" {
	#include "asf.h"
}

#include "buttons.h"
#include "events.h"

/** D38 = PC6 on PIOC */
#define BUTTON_D38_MASK  PIO_PC6

/** Debounce: SLCK / (DIV+1). DIV=655 -> ~20 ms at 32 kHz */
#define BUTTON_DEBOUNCE_DIV  655u

static void button_d38_handler(uint32_t id, uint32_t mask);

void init_buttons(void)
{
	sysclk_enable_peripheral_clock(ID_PIOC);

	/* Select debounce (not glitch) filter for PC6 */
	PIOC->PIO_DIFSR = BUTTON_D38_MASK;
	/* Enable input filter for PC6 */
	PIOC->PIO_IFER = BUTTON_D38_MASK;
	/* Debounce clock = SLCK / (DIV+1) */
	PIOC->PIO_SCDR = PIO_SCDR_DIV(BUTTON_DEBOUNCE_DIV);

	/* Rising-edge interrupt, priority 5 */
	pio_handler_set(PIOC, ID_PIOC, BUTTON_D38_MASK, PIO_IT_RISE_EDGE, button_d38_handler);
	pio_enable_interrupt(PIOC, BUTTON_D38_MASK);
	pio_handler_set_priority(PIOC, PIOC_IRQn, 5);
}

static void button_d38_handler(uint32_t id, uint32_t mask)
{
	(void)id;
	(void)mask;
	stop_sys_timer();
}
