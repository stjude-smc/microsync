/**
 * @file props.h
 * @author Roman Kiselev (roman.kiselev@stjude.org)
 * @brief System properties management interface.
 * 
 * This module provides a flexible property system for managing device configuration
 * and status information. Properties can be read-only, read-write, or write-only,
 * and can be backed by internal values, external variables, or function calls.
 * 
 * @version \projectnumber
 */

#pragma once

#include "globals.h"


/**
 * @brief System property identifiers.
 * 
 * Enumeration of all available system properties. Properties prefixed with 'ro_'
 * are read-only, 'rw_' are read-write, and 'wo_' are write-only.
 */
enum SysProps {
	ro_VERSION,                    /**< Device version number (read-only) */
	ro_SYS_TIMER_STATUS,           /**< System timer running status (read-only) */
	ro_SYS_TIMER_VALUE,            /**< Current system timer value (read-only) */
	ro_SYS_TIMER_OVF_COUNT,        /**< System timer overflow count (read-only) */
	ro_SYS_TIME_ms,                /**< Current system time in milliseconds (read-only) */
	ro_SYS_TIMER_PRESCALER,        /**< System timer prescaler value (read-only) */
	rw_DFLT_PULSE_DURATION_us,     /**< Default pulse duration in microseconds (read-write) */
	ro_WATCHDOG_TIMEOUT_ms,        /**< Watchdog timeout in milliseconds (read-only) */
	ro_N_EVENTS,                   /**< Number of events in queue (read-only) */
	rw_INTLCK_ENABLED,             /**< Laser interlock enabled state (read-write) */

	// pTIRF extension
	rw_SELECTED_LASERS,            /**< Selected laser mask (read-write) */
	wo_OPEN_SHUTTERS,              /**< Open all shutters (write-only) */
	wo_CLOSE_SHUTTERS,             /**< Close all shutters (write-only) */
	rw_SHUTTER_DELAY_us,           /**< Shutter delay in microseconds (read-write) */
	rw_CAM_READOUT_us,             /**< Camera readout time in microseconds (read-write) */
	rw_CAM_GLOBAL_RESET,           /**< Camera global reset in level trigger mode (read-write) */
};

/**
 * @brief Property access control enumeration.
 * 
 * Defines the access permissions for properties.
 */
enum class PropertyAccess {
	ReadOnly,   /**< Property can only be read */
	ReadWrite,  /**< Property can be read and written */
	WriteOnly   /**< Property can only be written */
};

/**
 * @brief Function pointer type for property getter functions.
 * 
 * Functions of this type return the current value of a property.
 */
using PropGetter = uint32_t (*)();

/**
 * @brief Function pointer type for property setter functions.
 * 
 * Functions of this type set the value of a property.
 * @param value The new value to set
 */
using PropSetter = void (*)(uint32_t);

/**
 * @brief Base class for all device properties.
 * 
 * Abstract base class that defines the interface for all property types.
 * Properties can be backed by internal values, external variables, or functions.
 */
class DeviceProperty {
public:
	/**
	 * @brief Constructor.
	 * @param access Access control for this property
	 */
	explicit DeviceProperty(PropertyAccess access) : access(access) {}
	
	/**
	 * @brief Virtual destructor.
	 */
	virtual ~DeviceProperty() = default;

	/**
	 * @brief Get the current value of the property.
	 * @return Current property value
	 */
	virtual uint32_t get_value() const = 0;
	
	/**
	 * @brief Set the value of the property.
	 * @param newValue New value to set
	 */
	virtual void set_value(uint32_t newValue) = 0;

protected:
	PropertyAccess access; /**< Access control for this property */
};

/**
 * @brief Property backed by an internal value.
 * 
 * Stores the property value internally within the property object.
 */
class InternalProperty : public DeviceProperty {
private:
	uint32_t value; /**< Internal value storage */

public:
	/**
	 * @brief Constructor.
	 * @param value Initial value for the property
	 * @param access Access control (default: ReadOnly)
	 */
	InternalProperty(uint32_t value, PropertyAccess access = PropertyAccess::ReadOnly);

	/**
	 * @brief Get the internal value.
	 * @return Current internal value
	 */
	uint32_t get_value() const override;
	
	/**
	 * @brief Set the internal value.
	 * @param new_value New value to store
	 */
	void set_value(uint32_t new_value) override;
};

/**
 * @brief Property backed by an external variable.
 * 
 * References an external variable for storage, allowing the property
 * to reflect changes to the external variable.
 */
class ExternalProperty : public DeviceProperty {
private:
	uint32_t* externalValue; /**< Pointer to external value storage */

public:
	/**
	 * @brief Constructor.
	 * @param externalValue Pointer to external variable
	 * @param access Access control (default: ReadOnly)
	 */
	ExternalProperty(uint32_t* externalValue, PropertyAccess access = PropertyAccess::ReadOnly);

	/**
	 * @brief Get the external value.
	 * @return Current value of the external variable
	 */
	uint32_t get_value() const override;
	
	/**
	 * @brief Set the external value.
	 * @param new_value New value to set in the external variable
	 */
	void set_value(uint32_t new_value) override;
};

/**
 * @brief Property backed by function calls.
 * 
 * Uses getter and setter functions to access the property value,
 * allowing for computed or complex property implementations.
 */
class FunctionProperty : public DeviceProperty {
private:
	PropGetter getter; /**< Function to get the property value */
	PropSetter setter; /**< Function to set the property value */

public:
	/**
	 * @brief Constructor.
	 * @param getter Function to get the property value
	 * @param setter Function to set the property value
	 * @param access Access control (default: ReadOnly)
	 */
	FunctionProperty(PropGetter getter, PropSetter setter, PropertyAccess access = PropertyAccess::ReadOnly);

	/**
	 * @brief Get the value via getter function.
	 * @return Value returned by the getter function
	 */
	uint32_t get_value() const override;
	
	/**
	 * @brief Set the value via setter function.
	 * @param new_value Value to pass to the setter function
	 */
	void set_value(uint32_t new_value) override;
};



/**
 * @brief Initialize the property system.
 * 
 * Creates and registers all system properties with their appropriate
 * access controls and backing implementations.
 */
void init_props();

/**
 * @brief Get the value of a system property.
 * @param prop Property identifier to retrieve
 * @return Current value of the property, or 0 if property not found
 * 
 * Retrieves the current value of the specified system property.
 * For read-only and read-write properties only.
 */
uint32_t get_property(SysProps prop);

/**
 * @brief Set the value of a system property.
 * @param prop Property identifier to set
 * @param value New value for the property
 * 
 * Sets the value of the specified system property.
 * For read-write and write-only properties only.
 */
void set_property(SysProps prop, uint32_t value);
