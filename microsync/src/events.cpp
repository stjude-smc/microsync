/*
 * sd_events.c
 *
 * Created: 9/9/2024 5:09:35 PM
 *  Author: rkiselev
 */ 



#include "events.h"

volatile uint32_t default_pulse_duration_us = 100;

// Create a table of events
std::priority_queue<Event> event_queue;

volatile bool sys_timer_running = false;
volatile uint64_t sys_tc_ovf_count = 0;

/************************************************************************/
/*                  INTERNAL FUNCTION PROTOTYPES                        */
/************************************************************************/
static inline void _update_ra();
static inline void _enable_event_irq();
static inline void _disable_event_irq();
static inline bool _update_event(Event *event);
static inline void _enqueue_event(const Event* event);  // thread-safe

/************************************************************************/
/*                 EVENT PROCESSING                                     */
/************************************************************************/

void process_events()
{
	static Event event;
	
	_disable_event_irq();
		while (!event_queue.empty())
		{
			// Keep processing events from the queue while they are pending
			event = event_queue.top();
			if (event.ts64_cts > current_time_cts() + TS_TOLERANCE_CTS)  // it's a future event
			{
				// Update the RA register for compare interrupt
				tc_write_ra(SYS_TC, SYS_TC_CH, event.ts_lo32_cts);
				tc_write_rc(SYS_TC, SYS_TC_CH, event.ts_lo32_cts + 1);
				break;  // Our job is done
			}

			// Fire the event function
			event.func(event.arg1, event.arg2);
			event_queue.pop();  // remove the event from the queue, preserving order

			if (_update_event(&event))  // Needs to be rescheduled?
			{
				// Put updated event back, preserving order of the queue
				event_queue.push(event);
			}
		}
	_enable_event_irq();
}


void init_burst_timer()
{
	sysclk_enable_peripheral_clock(ID_TC6); // TC2, channel 0
	tc_init(TC2, 0,
	TC_CMR_TCCLKS_TIMER_CLOCK1 |  // same time unit as the main clock
	TC_CMR_WAVE |          // waveform mode
	TC_CMR_ASWTRG_SET |  // set on timer start
	TC_CMR_ACPA_CLEAR |      // clear on compare event A
	TC_CMR_ACPC_SET |    // set on compare event C
	TC_CMR_WAVSEL_UP_RC    // reset timer on event C
	);
}

// Process the event metadata
static inline bool _update_event(Event *event)
{
	if (event->interv_cts >= MIN_EVENT_INTERVAL) // repeating event
	{
		event->ts64_cts += event->interv_cts;
		if (event->N == 0){  // infinite event - reschedule
			return true;
		}
		// if (N == 1), it was a last call, and we drop it
		if (event->N > 1) {  // reschedule the event
			event->N--;
			return true;
		}
	}
	return false;
}

/************************************************************************/
/*             EVENT SCHEDULING                                         */
/************************************************************************/

// Create an Event with data from a DataPacket.
// All timestamps are converted from microseconds to SYS_TC counts
// NOTE: you will have to deallocate memory yourself!
Event* event_from_datapacket(const DataPacket* packet, EventFunc func)
{
	Event* new_event = new Event();
	// Copy fields from DataPacket to Event
	new_event->func = func;
	new_event->arg1 = packet->arg1;
	new_event->arg2 = packet->arg2;
	new_event->ts64_cts = us2cts(packet->ts_us) + UNIFORM_TIME_DELAY_CTS;
	
	// N is 1 (one-time event) if interval is too small
	new_event->N = (packet->interv_us < MIN_EVENT_INTERVAL) ? 1 : packet->N;
	new_event->interv_cts = us2cts(packet->interv_us);
	
	return new_event;
}


// Schedule event relative to t=0
void schedule_event(const Event *event_p, bool relative)
{
	static Event relative_event;
	
	// Do we have enough memory?
	if (event_queue.size() >= MAX_N_EVENTS)
	{
		uart_tx("ERR: event table is full!\n");
		return;
	}
	
	if (relative & sys_timer_running)
	{
		relative_event = *event_p;
		relative_event.ts64_cts += current_time_cts();

		_enqueue_event(&relative_event);
	}
	else
	{
		_enqueue_event(event_p);
	}

	_update_ra();
}


static inline void _update_ra()
{
	static Event next_event;

	_disable_event_irq();
		next_event = event_queue.top();
		// Update the RA register for compare interrupt
		tc_write_ra(SYS_TC, SYS_TC_CH, next_event.ts64_cts);
		tc_write_rc(SYS_TC, SYS_TC_CH, next_event.ts64_cts + 1);
	_enable_event_irq();
}

static inline void _enqueue_event(const Event* event)
{
	_disable_event_irq();
		event_queue.push(*event);
	_enable_event_irq();
	// in case we missed any events while messing with the queue
	if (sys_timer_running)
	{
		process_events();
	}
}

// Schedule an electric level event on a given pin
// data->arg1 is the pin name (e.g. "A3")
// data->arg2 is polarity (0 or 1)
void schedule_pin(const DataPacket *data)
{
	Event* event_p = event_from_datapacket(data, set_pin_event_func);

	// Convert pin name to ioport index for the event function
	event_p->arg1 = pin_name_to_ioport_id(data->arg1);

	schedule_event(event_p);
	delete event_p;
}


// Schedule an electric pulse event on a given pin
// data->arg1 is the pin name (e.g. "A3")
// data->arg2 is the pulse duration in us
void schedule_pulse(const DataPacket *data, bool is_positive)
{
	Event* event_p = event_from_datapacket(data, set_pin_event_func);

	// Convert pin name to ioport index for the event function
	event_p->arg1 = pin_name_to_ioport_id(data->arg1);
	event_p->arg2 = is_positive ? 1 : 0;

	// Schedule front of the pulse
	if (sys_timer_running)
	{
		event_p->ts64_cts += current_time_cts();
	}
	
	schedule_event(event_p, false);

	// Schedule back of the pulse
	event_p->ts64_cts += us2cts((data->arg2 > 0) ? data->arg2 : default_pulse_duration_us);
	event_p->arg2 = is_positive ? 0 : 1;
	schedule_event(event_p, false);

	delete event_p;
}


void schedule_pulse(uint32_t pin_idx, uint32_t pulse_duration_us, uint64_t timestamp_us,
                    uint32_t N, uint32_t interval_us, bool relative)
{
	uint64_t now_cts = relative ? current_time_cts() : 0;
	
	Event event;
	event.func = set_pin_event_func;
	event.arg1 = pin_idx;
	event.arg2 = 1;  // rising edge
	event.ts64_cts = us2cts(timestamp_us) + now_cts;
	event.N = N;
	event.interv_cts = us2cts(interval_us);
	schedule_event(&event, false);
	
	event.arg2 = 0;  // falling edge
	event.ts64_cts += us2cts(pulse_duration_us);
	schedule_event(&event, false);
}


// Schedule an electric level change event on a given pin
// data->arg1 is the pin name (e.g. "A3")
// data->arg2 is ignored
void schedule_toggle(const DataPacket *data)
{
	Event* event_p = event_from_datapacket(data, tgl_pin_event_func);

	// Convert pin name to ioport index for the event function
	event_p->arg1 = pin_name_to_ioport_id(data->arg1);

	schedule_event(event_p);
	delete event_p;
}


void schedule_burst(const DataPacket *data)
{
	Event* event_p = event_from_datapacket(data, start_burst_func);

	// Convert us to TC2[0] counts (runs at 42MHz)
	event_p->arg1 = data->arg1 * 42;

	// Schedule front of the burst
	if (sys_timer_running)
	{
		event_p->ts64_cts += current_time_cts();
	}
	
	schedule_event(event_p, false);

	// Schedule stop of the burst
	event_p->func = stop_burst_func;
	event_p->ts64_cts += us2cts((data->arg2 > 0) ? data->arg2 : default_pulse_duration_us);
	schedule_event(event_p, false);

	delete event_p;
}


void schedule_enable_pin(const DataPacket *data)
{
	Event* event_p = event_from_datapacket(data, enable_pin_func);

	// Convert pin name to ioport index for the event function
	event_p->arg1 = pin_name_to_ioport_id(data->arg1);

	schedule_event(event_p);
	delete event_p;
}

void schedule_disable_pin(const DataPacket *data)
{
	Event* event_p = event_from_datapacket(data, disable_pin_func);

	// Convert pin name to ioport index for the event function
	event_p->arg1 = pin_name_to_ioport_id(data->arg1);

	schedule_event(event_p);
	delete event_p;
}

/************************************************************************/
/*                 FUNCTION TO USE WITHIN EVENTS                        */
/************************************************************************/

void tgl_pin_event_func(uint32_t arg1_pin_idx, uint32_t arg2_unused)
{
	pins[arg1_pin_idx].toggle();
}

void set_pin_event_func(uint32_t arg1_pin_idx, uint32_t arg2_level)
{
	pins[arg1_pin_idx].set_level(arg2_level);
}

void start_burst_func(uint32_t arg1_period, uint32_t arg2_unused)
{
	tc_stop(TC2, 0);
	TC2->TC_CHANNEL[0].TC_RA = arg1_period >> 3; // 1/8th of the period
	TC2->TC_CHANNEL[0].TC_RC = arg1_period;
	pio_set_peripheral(PIOC, PIO_PERIPH_B, PIO_PC25);
	tc_start(TC2, 0);
}

void stop_burst_func(uint32_t arg1_unused, uint32_t arg2_unused)
{
	tc_stop(TC2, 0);
	pio_set_output(PIOC, PIO_PC25, 0, 0, 0);
	pio_set_pin_low(PIO_PC25_IDX);
}

void enable_pin_func(uint32_t arg1_pin_idx, uint32_t arg2)
{
	pins[arg1_pin_idx].enable();
}

void disable_pin_func(uint32_t arg1_pin_idx, uint32_t arg2)
{
	pins[arg1_pin_idx].disable();
}

/************************************************************************/
/*                       SYSTEM TIMER CONTROL                           */
/************************************************************************/

// return current system time in microseconds
uint64_t current_time_us()
{
	return cts2us(current_time_cts());
}

// return current system time in seconds
float current_time_s()
{
	return ((float) cts2us(current_time_cts())) / 1000000.0;
}

// Start timer from 0
void start_sys_timer()
{
	if (!sys_timer_running)
	{
		sys_timer_running = true;
		tc_start(SYS_TC, SYS_TC_CH);
	}
}

// Stop system timer
void stop_sys_timer()
{
	sys_timer_running = false;
	sys_tc_ovf_count = 0;
	tc_stop(SYS_TC, SYS_TC_CH);
}


void init_sys_timer()
{
	sysclk_enable_peripheral_clock(ID_SYS_TC);
	
	tc_init(SYS_TC, SYS_TC_CH,
			SYS_TC_CMR_TCCLKS_TIMER_CLOCK |
			TC_CMR_WAVE |
			TC_CMR_ASWTRG_CLEAR | // clear PB25 on timer start
			TC_CMR_ACPA_SET |     //   set PB25 on compare event A
			TC_CMR_ACPC_CLEAR     // clear PB25 on compare event C
	);
	
	// Activate TIOA0 output
	pio_set_peripheral(PIOB, PIO_PERIPH_B, PIO_PB25);
	
	// Enable the interrupt on register compare
	_enable_event_irq();
	
	// Enable interrupt on overflow
	tc_enable_interrupt(SYS_TC, SYS_TC_CH, TC_IER_COVFS);
	
	NVIC_EnableIRQ(SYS_TC_IRQn);
	NVIC_SetPriority(SYS_TC_IRQn, 1); // The highest priority is 0 (reserved for watchdog)
}

// This re-adjusts timestamps of scheduled events so we can pause and continue
void pause_sys_timer()
{
	tc_stop(SYS_TC, SYS_TC_CH);
	//uint32_t stopped_at = tc_read_cv(SYS_TC, SYS_TC_CH);
	
	// update all pending events in the event table
	printf("ERR: pause_sys_timer() - NOT IMPLEMENTED");
}


/************************************************************************/
/*                  SYSTEM TIMER INTERRUPTS                             */
/************************************************************************/

// This interrupt runs when current time reaches the timestamp of the next
// scheduled event in the event_queue. We might end up processing more than
// one event.
void SYS_TC_Handler()
{
    // Read Timer Counter Status to clear the interrupt flag
	uint32_t status = tc_get_status(SYS_TC, SYS_TC_CH);
	
    if (status & TC_SR_CPAS) {  // RA match
		process_events();
    }

    if (status & TC_SR_COVFS) {  // overflow
	    sys_tc_ovf_count += (1ULL << 32);
    }
}

// Disable system timer interrupt on register A compare
static inline void _disable_event_irq()
{
	SYS_TC->TC_CHANNEL[SYS_TC_CH].TC_IDR = TC_IDR_CPAS;
}

// Enable system timer interrupt on register A compare
static inline void _enable_event_irq()
{
	SYS_TC->TC_CHANNEL[SYS_TC_CH].TC_IER = TC_IER_CPAS;
}
