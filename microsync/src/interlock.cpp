/*
 * interlock.cpp
 *
 * Created: 10/23/2024 5:08:52 PM
 *  Author: rkiselev
 */ 

#include "interlock.h"
#include "globals.h"
#include "pins.h"

/** @brief First interlock condition match flag */
volatile bool intlck_match_1 = false;

/** @brief Second interlock condition match flag */
volatile bool intlck_match_2 = false;

/** @brief Global laser enable/disable state */
volatile bool lasers_enabled = true;

/** @brief Interlock system enabled state */
bool interlock_enabled = true;

/**
 * @brief Initialize the interlock timer/counter
 * 
 * Sets up a timer/counter for laser interlock monitoring with heartbeat generation.
 */
void _init_interlock_timer()
{
    sysclk_enable_peripheral_clock(ID_INTLCK_TC);
    tc_init(INTLCK_TC, INTLCK_TC_CH,
        SYS_TC_CMR_TCCLKS_TIMER_CLOCK |  // same prescaler as the system timer
        TC_CMR_WAVE |                 // waveform generation mode
        TC_CMR_EEVT_XC0 |             // External event selection - enables TIOB
        TC_CMR_WAVSEL_UP_RC       // restart timer on event C
    );

    tc_write_rb(INTLCK_TC, INTLCK_TC_CH, us2cts(INTLCK_TC_PERIOD_US >> 4));
    tc_enable_interrupt(INTLCK_TC, INTLCK_TC_CH, TC_IER_CPBS);

    tc_write_rc(INTLCK_TC, INTLCK_TC_CH, us2cts(INTLCK_TC_PERIOD_US));
    tc_enable_interrupt(INTLCK_TC, INTLCK_TC_CH, TC_IER_CPCS);
    
    NVIC_EnableIRQ(INTLCK_TC_IRQn);
    NVIC_SetPriority(INTLCK_TC_IRQn, 3); // The highest priority is 0 (reserved for watchdog)
}


void init_interlock()
{
    _init_interlock_timer();

    sysclk_enable_peripheral_clock(ioport_pin_to_port_id(INTLCK_OUT));

    ioport_set_pin_mode(INTLCK_OUT, 0);
	ioport_set_pin_dir(INTLCK_OUT, IOPORT_DIR_OUTPUT);

    tc_start(INTLCK_TC, INTLCK_TC_CH);
}


void enable_lasers()
{
	lasers_enabled = true;

    // Update pin state to reflect the interlock state
    for (uint32_t i = 0; i < 4; ++i)
    {
        pins[shutter_pins[i]].update();
        pins[shutter_secondary_pins[i]].update();
    }
}


void disable_lasers()
{
	lasers_enabled = false;

    // Update pin state to reflect the interlock state
    for (uint32_t i = 0; i < 4; ++i)
    {
        pins[shutter_pins[i]].update();
        pins[shutter_secondary_pins[i]].update();
    }
}


void INTLCK_TC_Handler()
{
    // Read Timer Counter Status to clear the interrupt flag
    uint32_t status = tc_get_status(INTLCK_TC, INTLCK_TC_CH);
	
    // RB match - output goes from high to low
    if (status & TC_SR_CPBS) {
		// Verify that previous input is HIGH
        intlck_match_1 = ioport_get_pin_level(INTLCK_IN) == 1;
		
		// Drop the output to LOW and let it settle
		ioport_set_pin_level(INTLCK_OUT, 0);
    }

    // RC match - output went from low to high
    if (status & TC_SR_CPCS) {
		// Verify that previous input is LOW
		intlck_match_2 = ioport_get_pin_level(INTLCK_IN) == 0;
		
		// Set the output to HIGH and let it settle
		ioport_set_pin_level(INTLCK_OUT, 1);
    }
    
	if (interlock_enabled)
	{
		// Check if both conditions match
		if (intlck_match_1 && intlck_match_2)
		{
			if (!lasers_enabled)
			{
				enable_lasers();
			}
		}
		else
		{
			if (lasers_enabled)
			{
				disable_lasers();
			}
		}
	}
	else
	{
		// ignore interlock status, enable the lasers
		if (!lasers_enabled)
		{
			enable_lasers();
		}
	}
}

