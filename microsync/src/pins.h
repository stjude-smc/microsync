/**
 * @file pins.h
 * @author Roman Kiselev (roman.kiselev@stjude.org)
 * @brief Pin management and control interface.
 * 
 * This module provides pin mapping, configuration, and control functions for
 * the Arduino Due microcontroller. It includes support for digital and analog pins
 * with state management and safety features.
 * 
 * @version \projectnumber
 */

#pragma once

#include <asf.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "globals.h"

/**
 * @brief Error code returned when pin name is not found.
 * 
 * This value is used to indicate an invalid pin index and should be checked
 * by callers before using the returned value.
 */
#define INVALID_PIN_IDX UINT32_MAX

/**
 * @brief Convert pin name string to IOPORT ID.
 * @param pin_name Pointer to pin name string (e.g., "D13", "A0")
 * @return IOPORT ID for the specified pin, or INVALID_PIN_IDX if not found
 * 
 * Maps Arduino Due pin names to their corresponding IOPORT identifiers.
 */
uint32_t pin_name_to_ioport_id(const char* pin_name);

/**
 * @brief Convert pin name integer to IOPORT ID.
 * @param pin_name Pin name as integer (e.g., 13 for D13)
 * @return IOPORT ID for the specified pin, or INVALID_PIN_IDX if not found
 * 
 * Maps Arduino Due pin numbers to their corresponding IOPORT identifiers.
 */
uint32_t pin_name_to_ioport_id(const uint32_t pin_name);

/**
 * @brief Pin mapping structure for Arduino Due.
 * 
 * Maps pin names to their corresponding IOPORT indices for lookup.
 */
typedef struct {
	const char *pin_name; /**< Pin name string (e.g., "D13", "A0") */
	uint32_t pin_idx;     /**< IOPORT index for the pin */
} pin_map_t;

/**
 * @brief Global pin mapping array for Arduino Due.
 * 
 * Contains mappings for all digital and analog pins on the Arduino Due.
 */
extern const pin_map_t pin_map[];

/**
 * @brief Pin control class for managing individual pin states.
 * 
 * Provides methods for setting pin levels, enabling/disabling pins,
 * and managing pin state with safety checks.
 */
class Pin {
private:
	bool level;  /**< Current logical level of the pin */
	bool active; /**< Whether the pin is enabled/active */

public:
	uint32_t pin_idx; /**< IOPORT index for this pin */
	
	/**
	 * @brief Default constructor.
	 * 
	 * Initializes pin with level=false and active=true.
	 */
	Pin() : level(false), active(true) {};
	
	/**
	 * @brief Set the logical level of the pin.
	 * @param level The logical level to set (true=high, false=low)
	 * 
	 * Updates the internal state but doesn't immediately apply to hardware.
	 */
	void set_level(bool level);
	
	/**
	 * @brief Apply the current pin state to hardware.
	 * 
	 * Updates the actual pin output based on current level and active state.
	 */
	void update();
	
	/**
	 * @brief Toggle the pin level.
	 * 
	 * Inverts the current logical level of the pin.
	 */
	void toggle();
	
	/**
	 * @brief Enable the pin.
	 * 
	 * Sets the pin as active, allowing it to be controlled.
	 */
	void enable();
	
	/**
	 * @brief Disable the pin.
	 * 
	 * Sets the pin as inactive, preventing control operations.
	 */
	void disable();
	
	/**
	 * @brief Check if the pin is active.
	 * @return true if the pin is enabled, false otherwise
	 */
	bool is_active();
};

/**
 * @brief Global array of pin objects.
 * 
 * Contains Pin objects for all 107 pins on the Arduino Due.
 */
extern Pin pins[107];

/**
 * @brief Initialize all pins.
 * 
 * Sets up all pins with default configurations and enables
 * the pin control system.
 */
void init_pins();