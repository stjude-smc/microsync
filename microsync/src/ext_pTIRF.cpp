/*
 * ext_pTIRF.cpp
 *
 * Created: 10/28/2024 9:25:32 PM
 *  Author: rkiselev
 */ 

#include "ext_pTIRF.h"
#include "events.h"
#include "props.h"
#include <cstdint>
#include <algorithm>


/************************************************************************/
/*                 HELPER FUNCTIONS                                     */
/************************************************************************/

int _count_set_bits(unsigned int bitmask) {
	int count = 0;
	while (bitmask) {
		count += bitmask & 1; // Increment count if the last bit is set
		bitmask >>= 1;        // Right shift the bitmask by 1
	}
	return count;
}

/************************************************************************/
/*                SHORTCUTS FOR SHUTTER CONTROL                         */
/************************************************************************/

void open_shutters(uint32_t mask)
{
	if (mask == 0)
	{
		mask = 0b1111;
	}
	for (uint32_t i = 0; i < 4; ++i)
	{
		if (mask & (1 << i))
		{
			pins[shutter_pins[i]].set_level(true);
			pins[shutter_secondary_pins[i]].set_level(true);
		}
	}
}

void close_shutters(uint32_t mask)
{
	if (mask == 0)
	{
		mask = 0b1111;
	}
	for (uint32_t i = 0; i < 4; ++i)
	{
		if (mask & (1 << i))
		{
			pins[shutter_pins[i]].set_level(false);
			pins[shutter_secondary_pins[i]].set_level(false);
		}
	}
}

void select_lasers(uint32_t mask)
{
	for (uint32_t i = 0; i < 4; ++i)
	{
		if (mask & (1 << i))
		{
			pins[shutter_pins[i]].enable();
			pins[shutter_secondary_pins[i]].enable();
		}
		else
		{
			pins[shutter_pins[i]].disable();
			pins[shutter_secondary_pins[i]].disable();
		}
	}
}

uint32_t selected_lasers()
{
	uint32_t mask = 0;
	for (uint32_t i = 0; i < 4; ++i)
	{
		if (pins[shutter_pins[i]].is_active())
		{
			mask |= (1 << i);
		}
	}
	return mask;
}

void schedule_shutter_pulse(uint64_t pulse_duration_us,
                            uint64_t timestamp_us, uint32_t N, uint32_t interval_us,
							bool relative)
{
	uint64_t now_cts = (relative && sys_timer_running) ? current_time_cts() : 0;
	
	Event event;
	event.func = open_shutters_func;
	event.arg1 = selected_lasers();
	event.ts64_cts = us2cts(timestamp_us) + now_cts;
	event.N = N;
	event.interv_cts = us2cts(interval_us);
	schedule_event(&event, false);
	
	// Only schedule closing if pulse duration is non-zero
	if (pulse_duration_us > 0) {
		event.func = close_shutters_func;
		event.ts64_cts += us2cts(pulse_duration_us);
		schedule_event(&event, false);
	}
}

// Functions that can be used within event queue
void open_shutters_func(uint32_t mask, uint32_t){open_shutters(mask);}
void close_shutters_func(uint32_t mask, uint32_t){close_shutters(mask);}


/************************************************************************/
/*              SHORTCUTS FOR ACQUISITION MODES                         */
/************************************************************************/

struct AcqParams {
	uint32_t exp;
	uint32_t readout;
	uint32_t shutter;
	uint64_t start;

	AcqParams(const DataPacket* data) {
		exp = data->arg1;
		readout = get_property(rw_CAM_READOUT_us);
		shutter = std::max(1UL, get_property(rw_SHUTTER_DELAY_us));
		// Calculate earliest possible start time (can't be in the past!)
		uint64_t earliest_start = std::max((uint64_t)readout, (uint64_t)shutter);  // either ASAP
		uint64_t requested_start = (uint64_t)data->ts_us;                           // or at requested timestamp
		start = std::max(earliest_start, requested_start) + current_time_us() + UNIFORM_TIME_DELAY;
	}
};


void start_continuous_acq(const DataPacket* data) {
    AcqParams p(data);

	// Safety checks
	// camera readout time cannot be longer than the exposure time in this mode
	p.readout = std::min(p.exp, get_property(rw_CAM_READOUT_us));
	// reduce camera pulse duration for very short exposure times
	uint32_t cam_pulse_duration = std::min(p.exp >> 1, (uint32_t)default_pulse_duration_us);

	uint32_t N = data->N;

	// Schedule shutter opening at p.start - p.shutter
	// For N==0: shutters stay open indefinitely
	// For N>0: shutters close after N frames + readout + shutter delay
	auto pulse_duration = (N == 0) ? uint64_t{0} : uint64_t{p.exp} * N + p.readout + p.shutter;
	
	schedule_shutter_pulse(
		pulse_duration,         // duration: 0=infinite, otherwise N frames + readout + shutter
		p.start - p.shutter,    // open shutters just before the first frame
		1, 0, false);           // just once

	// Sacrificial frame clears the sensor..
	schedule_pulse(CAMERA_PIN, cam_pulse_duration, 
		p.start - p.readout - 250UL, // ..just before first frame, with margin
		1, 0, false);                // just once
  	
	// N + 1 camera pulses for N frames to acquire data, or infinite if N==0
    schedule_pulse(CAMERA_PIN, cam_pulse_duration,
		p.start,                 // first frame begins exactly at the start time
		(N == 0) ? 0 : (N + 1),  // 0 means infinite
		p.exp, false);           // the pulse interval is equal to the exposure time
}


// Helper function to calculate frame duration for stroboscopic imaging
uint32_t find_strobe_frame_duration(const AcqParams& p) {
	if (get_property(rw_CAM_LEVEL_TRIGGER_MODE) == LVL_TRG_NORMAL)
		return p.exp + 2*p.readout + 25;  // exposure, double readout, and a small safety buffer
	return p.exp + p.readout + p.shutter;
}

// Helper function to calculate burst period based on frame duration and requested interval
uint32_t find_strobe_period(uint32_t frame_duration, uint32_t requested_interval, uint32_t multiplier = 1) {
    return std::max(multiplier * frame_duration, requested_interval);
}


// Helper function to schedule camera pulses for stroboscopic acquisition, depending on the level trigger mode property
void schedule_camera_strobe(const AcqParams& p, uint32_t frame_start, uint32_t N, uint32_t period) {
	uint32_t cam_pulse_duration;
	uint32_t cam_start;

	switch (get_property(rw_CAM_LEVEL_TRIGGER_MODE)) {
		default: 
		case LVL_TRG_NORMAL:
		case LVL_TRG_OVERLAP:
			cam_pulse_duration = p.exp + p.readout;
			cam_start = frame_start - p.readout;
			break;
		case LVL_TRG_GLOBAL_RESET:
			cam_pulse_duration = p.exp;
			cam_start = frame_start;
			break;
	}

    schedule_pulse(CAMERA_PIN, cam_pulse_duration, cam_start, N, period, false);
}

void start_stroboscopic_acq(const DataPacket* data) {
    AcqParams p(data);
    
    // Calculate burst period: at least exposure time + readout + shutter delay, or the requested interval
    uint32_t frame_duration = find_strobe_frame_duration(p);
    uint32_t burst_period = find_strobe_period(frame_duration, data->interv_us);
    
    // Schedule N shutter pulses, each just before the frame starts
    schedule_shutter_pulse(p.exp, p.start - p.shutter, data->N, burst_period, false);

    // Schedule N camera pulses
    schedule_camera_strobe(p, p.start, data->N, burst_period);
}


void start_ALEX_acq(const DataPacket* data) {
    AcqParams p(data);

    // Count enabled lasers and calculate timing
    uint32_t N_ch = _count_set_bits(selected_lasers());
    uint32_t frame_duration = find_strobe_frame_duration(p);
    uint32_t burst_period = find_strobe_period(frame_duration, data->interv_us, N_ch);

	// Schedule pulses for each enabled laser
	for (uint32_t i = 0; i < 4; ++i) {
	    if (pins[shutter_pins[i]].is_active()) {
			// Laser pulse: open shutter just before frame starts, pulse for exposure duration
		    schedule_pulse(
				pins[shutter_pins[i]].pin_idx, // selected laser
				p.exp, 				           // pulse duration is the exposure time
				p.start - p.shutter,           // open shutters just before the frame starts
				data->N,                       // N pulses for N bursts (times number of lasers)
				burst_period,                  // once per laser per burst period
				false);

			// Camera pulse: synchronized with laser pulse
		    schedule_camera_strobe(p, p.start, data->N, burst_period);

			// Move to the next frame within the burst
		    p.start += frame_duration;
	    }
    }
}
