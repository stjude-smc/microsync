/**
 * @file events.h
 * @author Roman Kiselev (roman.kiselev@stjude.org)
 * @brief Event scheduling system for microsecond-precision timing control.
 * 
 * This module implements a priority queue-based event scheduler that provides
 * microsecond-precision timing control for microscope synchronization. The system
 * can handle up to 450 scheduled events with 64-bit timestamp precision.
 * 
 * @version \projectnumber
 */


#pragma once

#ifdef min
#undef min
#endif

#ifdef max
#undef max
#endif

#include <queue>          // priority queue, FIFO queue

#ifndef UNIT_TEST
#include <asf.h>
#include "pins.h"
#endif

#include "globals.h"
#include "uart_comm.h"

/**
 * @brief Default pulse duration in microseconds.
 * 
 * This value is used when no specific pulse duration is provided.
 * Can be modified at runtime via system properties.
 */
extern volatile uint32_t default_pulse_duration_us;

/**
 * @brief Function pointer type for event execution.
 * 
 * Event functions receive two 32-bit arguments and perform the actual
 * hardware control operations (pin setting, toggling, etc.).
 * 
 * @param arg1 First argument (typically pin index or duration)
 * @param arg2 Second argument (typically additional parameters)
 */
using EventFunc = void (*)(uint32_t, uint32_t);

/**
 * @brief Event structure for priority queue scheduling.
 * 
 * This structure represents a single scheduled event in the system.
 * Events are ordered by timestamp in a priority queue for precise execution.
 * The structure is packed to minimize memory usage.
 * 
 * @note The Event struct is 28 bytes in total. The event timestamp is stored as a 64-bit integer (ts64_cts), which can also be accessed as two 32-bit fields: ts_lo32_cts (lower 32 bits) and ts_hi32_cts (upper 32 bits).
 */
typedef struct  __attribute__((packed)) Event
{
	EventFunc func;            /**< Pointer to the function that will be executed for this event (4 bytes) */
	uint32_t	  arg1;        /**< First function argument (4 bytes) */
	uint32_t	  arg2;        /**< Second function argument (4 bytes) */
	union                      /**< 64-bit timestamp in clock ticks (8 bytes) */
	{
		uint64_t  ts64_cts;    /**< Full 64-bit timestamp, shared with ts_lo32_cts and ts_hi32_cts */
		struct {
			uint32_t ts_lo32_cts;  /**< Lower 32 bits of the 64-bit timestamp - value of the hardware timer/counter */
			uint32_t ts_hi32_cts;  /**< Upper 32 bits of the 64-bit timestamp - number of timer/counter overflows */
		};
	};
	uint32_t	  N;           /**< Number of remaining event repetitions (4 bytes) */
	uint32_t	  interv_cts;  /**< Interval between event repetitions in clock ticks (4 bytes) */

   // Constructor
   Event() : func([](uint32_t, uint32_t) { printf("ERR: Event func not set!\n"); }),
	   arg1(0), arg2(0), ts64_cts(0), N(0), interv_cts(0) {}


	bool operator<(const Event& other) const {
		return this->ts64_cts > other.ts64_cts;
	}
} Event;  // 28 bytes


/**
 * @brief Priority queue of scheduled events.
 * 
 * Events are automatically sorted by timestamp (earliest first).
 * The queue is processed by the system timer interrupt handler.
 */
extern std::priority_queue<Event> event_queue;

/**
 * @brief System timer overflow counter.
 * 
 * Tracks the number of timer overflows to maintain 64-bit precision
 * across the full time range of the system.
 */
extern volatile uint64_t sys_tc_ovf_count;

/**
 * @brief Create an event from a data packet.
 * 
 * Allocates memory and initializes an Event structure from the provided
 * data packet. If no function is specified, a default error handler is used.
 * 
 * @param packet Pointer to the data packet containing event parameters
 * @param func Optional function pointer (defaults to nullptr)
 * @return Pointer to the allocated Event structure
 */
Event* event_from_datapacket(const DataPacket* packet, EventFunc func=nullptr);

/**
 * @brief Schedule an event for execution.
 * 
 * Adds an event to the priority queue for execution at the specified time.
 * 
 * @param event Pointer to the event to schedule
 * @param relative If true, timestamp is relative to current time (default: true)
 */
void schedule_event(const Event *event, bool relative = true);

/**
 * @brief Schedule a pulse event from a data packet.
 * @param data Pointer to the data packet containing pulse parameters
 * @param is_positive If true, generate positive pulse; if false, negative pulse
 * 
 * Creates and schedules a pulse event based on the provided data packet.
 * The pulse will be generated on the pin specified in the data packet.
 */
void schedule_pulse(const DataPacket *data, bool is_positive);

/**
 * @brief Schedule a pulse event with explicit parameters.
 * @param pin_idx IOPORT index of the pin to pulse (see pin_map_t in pins.cpp for pin names)
 * @param pulse_duration_us Duration of the pulse in microseconds
 * @param timestamp_us Timestamp for the pulse in microseconds
 * @param N Number of pulses to generate
 * @param interval_us Interval between pulses in microseconds
 * @param relative If true, timestamp is relative to current time
 * 
 * Creates and schedules a pulse event with the specified parameters.
 * This function provides direct control over all pulse parameters.
 */
void schedule_pulse(uint32_t pin_idx, uint32_t pulse_duration_us, uint64_t timestamp_us,
                    uint32_t N, uint32_t interval_us, bool relative = true);

/**
 * @brief Schedule a pin set event from a data packet.
 * @param data Pointer to the data packet containing pin parameters
 * 
 * Creates and schedules a pin set event based on the provided data packet.
 * The pin will be set to the level specified in the data packet.
 */
void schedule_pin(const DataPacket *data);

/**
 * @brief Schedule a pin toggle event from a data packet.
 * @param data Pointer to the data packet containing pin parameters
 * 
 * Creates and schedules a pin toggle event based on the provided data packet.
 * The pin will be toggled at the specified time.
 */
void schedule_toggle(const DataPacket *data);

/**
 * @brief Schedule a burst event from a data packet.
 * @param data Pointer to the data packet containing burst parameters
 * 
 * Creates and schedules a burst event based on the provided data packet.
 * The burst will generate a train of pulses with the specified parameters.
 */
void schedule_burst(const DataPacket *data);

/**
 * @brief Schedule a pin enable event from a data packet.
 * @param data Pointer to the data packet containing pin parameters
 * 
 * Creates and schedules a pin enable event based on the provided data packet.
 * The pin will be enabled at the specified time.
 */
void schedule_enable_pin(const DataPacket *data);

/**
 * @brief Schedule a pin disable event from a data packet.
 * @param data Pointer to the data packet containing pin parameters
 * 
 * Creates and schedules a pin disable event based on the provided data packet.
 * The pin will be disabled at the specified time.
 */
void schedule_disable_pin(const DataPacket *data);

/**
 * @brief Process all pending events in the queue.
 * 
 * Checks the event queue and executes any events whose timestamps have been reached.
 * This function should be called regularly by the system timer interrupt handler.
 */
void process_events();

/**
 * @brief Initialize the burst timer.
 * 
 * Sets up the timer/counter used for generating burst pulse trains.
 * Configures the timer hardware and enables necessary interrupts.
 */
void init_burst_timer();

/**
 * @brief Initialize the system timer.
 * 
 * Sets up the main system timer/counter used for event scheduling.
 * Configures the timer hardware, prescaler, and interrupt handling.
 */
void init_sys_timer();

/**
 * @brief Start the system timer.
 * 
 * Enables the system timer and begins processing scheduled events.
 * Events will start executing at their specified timestamps.
 */
void start_sys_timer();

/**
 * @brief Stop the system timer.
 * 
 * Disables the system timer and halts event processing.
 * The event queue is preserved and can be resumed with start_sys_timer().
 */
void stop_sys_timer();

/**
 * @brief Pause the system timer.
 * 
 * Temporarily stops the system timer without clearing the event queue.
 * Event processing can be resumed with start_sys_timer().
 */
void pause_sys_timer();

/**
 * @brief System timer running state.
 * 
 * Indicates whether the system timer is currently running and processing events.
 */
extern volatile bool sys_timer_running;

/**
 * @brief Get current system time in native timer counts, including overflows.
 * @return Current system time in timer counts
 * 
 * Returns the current system time in native timer counts.
 * Uses the system timer and overflow counter for 64-bit precision.
 */
inline uint64_t current_time_cts()
{
	return (uint64_t) sys_timer_running * (sys_tc_ovf_count | SYS_TC->TC_CHANNEL[SYS_TC_CH].TC_CV);
}

/**
 * @brief Get current system time in microseconds.
 * @return Current system time in microseconds
 * 
 * Returns the current system time converted to microseconds.
 * Uses the system timer value and overflow counter for 64-bit precision.
 */
uint64_t current_time_us();

/**
 * @brief Get current system time in seconds.
 * @return Current system time in seconds as a float
 * 
 * Returns the current system time converted to seconds.
 * Uses the system timer value and overflow counter for 64-bit precision.
 */
float current_time_s();

/**
 * @brief Event function for toggling a pin.
 * @param arg1_pin_idx IOPORT index of the pin to toggle (see pin_map_t in pins.cpp for pin names)
 * @param arg2 Unused parameter (for event function compatibility)
 * 
 * Event callback function that toggles the state of the specified pin.
 * This function is used internally by the event system.
 */
void tgl_pin_event_func(uint32_t arg1_pin_idx, uint32_t arg2);

/**
 * @brief Event function for setting a pin level.
 * @param arg1_pin_idx IOPORT index of the pin to set (see pin_map_t in pins.cpp for pin names)
 * @param arg2 Pin level to set (0=low, 1=high)
 * 
 * Event callback function that sets the level of the specified pin.
 * This function is used internally by the event system.
 */
void set_pin_event_func(uint32_t arg1_pin_idx, uint32_t arg2);

/**
 * @brief Event function for starting a burst.
 * @param arg1_period Period of the burst in microseconds
 * @param arg2_unused Unused parameter (for event function compatibility)
 * 
 * Event callback function that starts a burst pulse train.
 * This function is used internally by the event system.
 */
void start_burst_func  (uint32_t arg1_period,  uint32_t arg2_unused);

/**
 * @brief Event function for stopping a burst.
 * @param arg1_unused Unused parameter (for event function compatibility)
 * @param arg2_unused Unused parameter (for event function compatibility)
 * 
 * Event callback function that stops a burst pulse train.
 * This function is used internally by the event system.
 */
void stop_burst_func   (uint32_t arg1_unused,  uint32_t arg2_unused);

/**
 * @brief Event function for enabling a pin.
 * @param arg1_pin_idx IOPORT index of the pin to enable (see pin_map_t in pins.cpp for pin names)
 * @param arg2 Unused parameter (for event function compatibility)
 * 
 * Event callback function that enables the specified pin.
 * This function is used internally by the event system.
 */
void enable_pin_func   (uint32_t arg1_pin_idx, uint32_t arg2);

/**
 * @brief Event function for disabling a pin.
 * @param arg1_pin_idx IOPORT index of the pin to disable (see pin_map_t in pins.cpp for pin names)	
 * @param arg2 Unused parameter (for event function compatibility)
 * 
 * Event callback function that disables the specified pin.
 * This function is used internally by the event system.
 */
void disable_pin_func  (uint32_t arg1_pin_idx, uint32_t arg2);

inline bool is_event_missed()
{
	static Event e;
	bool result = false;

	if (sys_timer_running && !event_queue.empty())
	{
		e = event_queue.top();
		result = current_time_cts() > (e.ts64_cts + TS_MISSED_TOLERANCE_CTS);
	}
	return result;
}
