/**
 * @file ext_pTIRF.h
 * @author Roman Kiselev (roman.kiselev@stjude.org)
 * @brief pTIRF microscope control extensions.
 * 
 * This module provides specialized functions for controlling pTIRF (photoactivated
 * Total Internal Reflection Fluorescence) microscopes. It includes shutter control,
 * laser selection, and acquisition mode functions optimized for pTIRF imaging.
 * 
 * @version \projectnumber
 */

#pragma once
#include "globals.h"
#include "uart_comm.h"

/**
 * @brief type of laser shutters to manipulate - primary or secondary
 */
enum ShutterType {
	SHUTTERS_BOTH = 0,		/**< Apply to both types of laser shutters */
	SHUTTERS_PRIMARY = 1,    /**< Apply only to primary laser shutters */
	SHUTTERS_SECONDARY = 2,  /**< Apply only to secondary laser shutters */
	};

/**
 * @brief Open laser shutters.
 * @param mask Bitmask specifying which shutters to open (0 = all shutters)
 * 
 * Opens the specified laser shutters. If mask is 0, opens all shutters.
 * Each bit in the mask corresponds to a laser: bit 0 = Cy2, bit 1 = Cy3, etc.
 */
void open_shutters(uint32_t mask = 0, uint32_t what_shutters = SHUTTERS_BOTH);

/**
 * @brief Close laser shutters.
 * @param mask Bitmask specifying which shutters to close (0 = all shutters)
 * 
 * Closes the specified laser shutters. If mask is 0, closes all shutters.
 * Each bit in the mask corresponds to a laser: bit 0 = Cy2, bit 1 = Cy3, etc.
 */
void close_shutters(uint32_t mask = 0, uint32_t what_shutters = SHUTTERS_BOTH);

/**
 * @brief Select which lasers are active.
 * @param mask Bitmask specifying which lasers to enable
 * 
 * Enables the specified lasers and disables all others.
 * Each bit in the mask corresponds to a laser: bit 0 = Cy2, bit 1 = Cy3, etc.
 */
void select_lasers(uint32_t mask);

/**
 * @brief Get currently selected lasers.
 * @return Bitmask of currently enabled lasers
 * 
 * Returns a bitmask indicating which lasers are currently enabled.
 * Each bit corresponds to a laser: bit 0 = Cy2, bit 1 = Cy3, etc.
 */
uint32_t selected_lasers();

/**
 * @brief Schedule a shutter pulse event.
 * @param pulse_duration_us Duration of the pulse in microseconds (0 = keep open indefinitely)
 * @param timestamp_us Timestamp for the pulse in microseconds
 * @param N Number of pulses to generate
 * @param interval_us Interval between pulses in microseconds
 * @param relative If true, timestamp is relative to current time
 * @param what_shutters Which shutters to pulse (primary/secondary/both), default SHUTTERS_BOTH
 * 
 * Schedules a series of shutter pulses with the specified parameters.
 * If pulse_duration_us is 0, only opening events are scheduled (shutters stay open).
 */
void schedule_shutter_pulse(uint64_t pulse_duration_us, uint64_t timestamp_us, uint32_t N, uint32_t interval_us, bool relative, uint32_t what_shutters = SHUTTERS_BOTH);

/**
 * @brief Event function wrapper for opening shutters.
 * @param mask Bitmask specifying which shutters to open
 * @param what_shutters Which shutters (primary/secondary/both)
 * 
 * Wrapper function that can be used as an event callback to open shutters.
 */
void open_shutters_func(uint32_t mask, uint32_t what_shutters);

/**
 * @brief Event function wrapper for closing shutters.
 * @param mask Bitmask specifying which shutters to close
 * @param what_shutters Which shutters (primary/secondary/both)
 * 
 * Wrapper function that can be used as an event callback to close shutters.
 */
void close_shutters_func(uint32_t mask, uint32_t what_shutters);

/**
 * @brief Property setter for open shutters (single-arg, applies to both primary and secondary).
 * @param mask Bitmask specifying which shutters to open
 */
void open_shutters_setter(uint32_t mask);

/**
 * @brief Property setter for close shutters (single-arg, applies to both primary and secondary).
 * @param mask Bitmask specifying which shutters to close
 */
void close_shutters_setter(uint32_t mask);

/**
 * @brief Start continuous acquisition mode.
 * @param data Data packet containing acquisition parameters
 * 
 * Initiates continuous image acquisition with the specified parameters.
 * This mode continuously captures images without synchronization.
 */
void start_continuous_acq(const DataPacket* data);

/**
 * @brief Start stroboscopic acquisition mode.
 * @param data Data packet containing acquisition parameters
 * 
 * Initiates stroboscopic image acquisition with laser pulsing.
 * This mode synchronizes laser pulses with camera exposure.
 */
void start_stroboscopic_acq(const DataPacket* data);

/**
 * @brief Start ALEX (Alternating Laser Excitation) acquisition mode.
 * @param data Data packet containing acquisition parameters
 * 
 * Initiates ALEX acquisition mode for fluorescence resonance energy transfer (FRET) imaging.
 * This mode alternates between different laser excitations.
 */
void start_ALEX_acq(const DataPacket* data);