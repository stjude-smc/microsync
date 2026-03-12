/**
 * @file globals.h
 * @author Roman Kiselev (roman.kiselev@stjude.org)
 * @brief Global system definitions: pinouts and settings.
 */
#pragma once

#ifndef UNIT_TEST
#include <ioport.h>
#include "pins.h"
#endif

#define VERSION "2.6.4"


/************************************************************************/
/*                    PINOUT AND WIRING DEFINITIONS                     */
/************************************************************************/
// Laser shutters
#define CY2_PIN		PIO_PC22_IDX	// D8
#define CY3_PIN		PIO_PC21_IDX	// D9
#define CY5_PIN		PIO_PA28_IDX	// D10
#define CY7_PIN		PIO_PD7_IDX  	// D11

#define CY2_SECONDARY_PIN PIO_PC2_IDX	// D34
#define CY3_SECONDARY_PIN PIO_PC1_IDX	// D33
#define CY5_SECONDARY_PIN PIO_PD10_IDX	// D32
#define CY7_SECONDARY_PIN PIO_PA7_IDX	// D31

#define SECONDARY_SHUTTER_DELAY 5000UL  // delay of the secondary shutters, in us. We assume it's mechanical

const uint32_t shutter_pins[] = { CY2_PIN, CY3_PIN, CY5_PIN, CY7_PIN };
const uint32_t shutter_secondary_pins[] = { CY2_SECONDARY_PIN, CY3_SECONDARY_PIN, CY5_SECONDARY_PIN, CY7_SECONDARY_PIN };

#define CAMERA_PIN  PIO_PC23_IDX    // D7

// Error indicator trigger
#define ERR_PIN		PIO_PC12_IDX	// D51

/**
 * @brief Turn on the error indicator LED.
 * 
 * Sets the error LED pin high to indicate an error condition.
 * The LED is connected to pin D53 on the Arduino Due.
 */
inline void err_led_on(){
	ioport_set_pin_level(ERR_PIN, 1);
}

/**
 * @brief Turn off the error indicator LED.
 * 
 * Sets the error LED pin low to clear the error indication.
 * The LED is connected to pin D53 on the Arduino Due.
 */
inline void err_led_off(){
	ioport_set_pin_level(ERR_PIN, 0);
}

// Debug pin
#define DBG_PIN  PIO_PB14_IDX        // D53

/**
 * @brief Set the debug pin high.
 * 
 * Sets the debug pin high for debugging and timing measurements.
 * The debug pin is connected to D31 on the Arduino Due.
 */
inline void dbg_pin_up(){
	ioport_set_pin_level(DBG_PIN, 1);
}

/**
 * @brief Set the debug pin low.
 * 
 * Sets the debug pin low for debugging and timing measurements.
 * The debug pin is connected to D31 on the Arduino Due.
 */
inline void dbg_pin_dn(){
	ioport_set_pin_level(DBG_PIN, 0);
}

// Burst pulse train pin
#define BURST_PIN    PIO_PC25_IDX	// D5, TIOA6  (TC2, channel 0)


// Interlock configuration (see datasheet table 36-4)
#define INTLCK_IN		      PIO_PD8_IDX   // D12

#define INTLCK_OUT       	  PIO_PB27_IDX      // D13, TIOB0  (TC0, channel 0)
#define INTLCK_OUT_PERIPH     IOPORT_MODE_MUX_B

#define ID_INTLCK_TC          ID_TC0
#define INTLCK_TC             TC0	// ID / 3
#define INTLCK_TC_CH          0		// ID % 3
#define INTLCK_TC_Handler     TC0_Handler
#define INTLCK_TC_IRQn		  TC0_IRQn
#define INTLCK_TC_PERIOD_US	  25000UL

/************************************************************************/
/*                    UART AND DMA CONFIGURATION                        */
/************************************************************************/
#define UART_BUFFER_SIZE 512   // Size of DMA-controlled UART buffers
#define UART_BAUDRATE 115200   // bits per second
#define UART_TIMEOUT  25       // ms - timeout for UART communication
// UART uses timer 4 (module TC1 channel 1)
#define ID_UART_TC           ID_TC4
#define UART_TC              TC1	// ID / 3
#define UART_TC_CH           1		// ID % 3
#define UART_TIMEOUT_Handler TC4_Handler
#define UART_TC_IRQn	     TC4_IRQn


/************************************************************************/
/*                      EVENT HANDLING                                  */
/************************************************************************/
#define WATCHDOG_TIMEOUT  100UL  // ms

// Maximum allowed number of events in the event table
#define MAX_N_EVENTS	450UL

// Uniform time delay added to every single scheduled event, us
// It should be long enough to ensure correct event processing
// under any circumstance
#define UNIFORM_TIME_DELAY 500UL

// Minimal interval between two subsequent runs of the same events, us
#define MIN_EVENT_INTERVAL 20UL

// Grace period for event processing - any event within this interval gets fired
#define TS_TOLERANCE        2UL   // us
#define TS_MISSED_TOLERANCE 100UL // us - when we decide the event has been missed


/************************************************************************/
/*    SYSTEM TIMER CONFIGURATION AND TIME CONVERSION FUNCTIONS          */
/************************************************************************/

// Timer prescaler configuration. See SAM3X TC_CMR register, datasheet p883
// Options are 2, 8, 32, and 128
#define PRESC32

#ifdef PRESC2    // 1ct = 24ns, overflow after 102s  (1min 42s)
#define SYS_TC_PRESCALER 2UL
#define SYS_TC_CMR_TCCLKS_TIMER_CLOCK TC_CMR_TCCLKS_TIMER_CLOCK1
#endif

#ifdef PRESC8    // 1ct = 95ns, overflow after 409s  (6min 49s)
#define SYS_TC_PRESCALER 8UL
#define SYS_TC_CMR_TCCLKS_TIMER_CLOCK TC_CMR_TCCLKS_TIMER_CLOCK2
#endif

#ifdef PRESC32   // 1ct = 381ns, overflow after 1636s (27min 16s)
#define SYS_TC_PRESCALER 32UL
#define SYS_TC_CMR_TCCLKS_TIMER_CLOCK TC_CMR_TCCLKS_TIMER_CLOCK3
#endif

#ifdef PRESC128  // 1ct = 1524ns, overflow after 6544s (1h 49min)
#define SYS_TC_PRESCALER 128UL
#define SYS_TC_CMR_TCCLKS_TIMER_CLOCK TC_CMR_TCCLKS_TIMER_CLOCK4
#endif

#define SYS_TC_CONVERSION_MULTIPLIER (8400000UL/SYS_TC_PRESCALER)
#define TS_TOLERANCE_CTS (TS_TOLERANCE * SYS_TC_CONVERSION_MULTIPLIER / 100000UL)
#define TS_MISSED_TOLERANCE_CTS (TS_MISSED_TOLERANCE * SYS_TC_CONVERSION_MULTIPLIER / 100000UL)
#define UNIFORM_TIME_DELAY_CTS (UNIFORM_TIME_DELAY * SYS_TC_CONVERSION_MULTIPLIER / 100000UL)

// microseconds to counts
static inline uint64_t us2cts(uint64_t us) {
	return us * SYS_TC_CONVERSION_MULTIPLIER / 100000ULL;
}

// counts to microseconds
static inline uint64_t cts2us(uint64_t cts) {
	return cts * 100000ULL / SYS_TC_CONVERSION_MULTIPLIER;
}


// Main timer/counter for events (module TC1 channel 0)
#define ID_SYS_TC		ID_TC3
#define SYS_TC			TC1		// ID / 3
#define SYS_TC_CH		0		// ID % 3
#define SYS_TC_Handler  TC3_Handler
#define SYS_TC_IRQn		TC3_IRQn

