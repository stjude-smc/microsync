/*
 * props.cpp
 *
 * Get/set system properties
 *
 * Created: 10/16/2024 2:59:57 PM
 *  Author: rkiselev
 */ 

#include <unordered_map>

#include "props.h"
#include "uart_comm.h"
#include "events.h"
#include "interlock.h"
#include "ext_pTIRF.h"


// Global map to store properties by their ID
/** @brief Global property map containing all system properties */
std::unordered_map<SysProps, DeviceProperty*> props;


/**
 * @brief Get the upper 32 bits of the system timer overflow count
 * @return Upper 32 bits of sys_tc_ovf_count
 */
uint32_t get_sys_tc_ovf(){return (uint32_t) (sys_tc_ovf_count >> 32);}

/**
 * @brief Get current system time in milliseconds
 * @return Current time in milliseconds
 */
uint32_t get_time_ms(){return (uint32_t) (cts2us(current_time_cts()) / 1000);}

/**
 * @brief Get the number of events in the event queue
 * @return Number of events currently in the queue
 */
uint32_t get_N_events(){return (uint32_t) event_queue.size();}




void init_props() {
	props[ro_SYS_TIMER_STATUS]       = new ExternalProperty((uint32_t*) &sys_timer_running);
	props[ro_SYS_TIMER_VALUE]        = new ExternalProperty((uint32_t*) &(SYS_TC->TC_CHANNEL[SYS_TC_CH].TC_CV));
	props[ro_SYS_TIMER_OVF_COUNT]    = new FunctionProperty(get_sys_tc_ovf, nullptr);
	props[ro_SYS_TIME_ms]            = new FunctionProperty(get_time_ms, nullptr);
	props[ro_SYS_TIMER_PRESCALER]    = new InternalProperty((uint32_t) SYS_TC_PRESCALER);
	props[rw_DFLT_PULSE_DURATION_us] = new ExternalProperty((uint32_t*) &default_pulse_duration_us, PropertyAccess::ReadWrite);
	props[ro_WATCHDOG_TIMEOUT_ms]    = new InternalProperty((uint32_t) WATCHDOG_TIMEOUT);
	props[ro_N_EVENTS]               = new FunctionProperty(get_N_events, nullptr);
	props[rw_INTLCK_ENABLED]         = new ExternalProperty((uint32_t*) &interlock_enabled, PropertyAccess::ReadWrite);

	// pTIRF extension
	props[rw_SELECTED_LASERS]        = new FunctionProperty(selected_lasers, select_lasers, PropertyAccess::ReadWrite);
	props[wo_OPEN_SHUTTERS]          = new FunctionProperty(nullptr, open_shutters, PropertyAccess::WriteOnly);
	props[wo_CLOSE_SHUTTERS]         = new FunctionProperty(nullptr, close_shutters, PropertyAccess::WriteOnly);
	props[rw_SHUTTER_DELAY_us]       = new InternalProperty(1000UL, PropertyAccess::ReadWrite);
	props[rw_CAM_READOUT_us]         = new InternalProperty(12000UL, PropertyAccess::ReadWrite);
	props[rw_CAM_GLOBAL_RESET]       = new InternalProperty(0UL, PropertyAccess::ReadWrite);
}



uint32_t get_property(SysProps id)
{
	auto iterator = props.find(id);
	if (iterator == props.end())
	{
		printf("ERR: Property not found (ID: %d)\n", id);
		return 0;
	}
	return iterator->second->get_value();
}


void set_property(SysProps id, uint32_t value)
{
    auto iterator = props.find(id);
    if (iterator == props.end()) {
        printf("ERR: Property not found (ID: %d)\n", id);
        return;
    }
    iterator->second->set_value(value);
}


// InternalProperty methods
InternalProperty::InternalProperty(uint32_t value, PropertyAccess access)
: DeviceProperty(access), value(value)
{
}

uint32_t InternalProperty::get_value() const
{
	if (access == PropertyAccess::ReadOnly || access == PropertyAccess::ReadWrite)
	{
		return value;
	}
	else
	{
		printf("ERR: property is WriteOnly\n");
		return 0;
	}
}

void InternalProperty::set_value(uint32_t new_value)
{
	if (access == PropertyAccess::ReadWrite || access == PropertyAccess::WriteOnly)
	{
		value = new_value;
	}
	else
	{
		printf("ERR: property is ReadOnly\n");
	}
}

// ExternalProperty methods
ExternalProperty::ExternalProperty(uint32_t* externalValue, PropertyAccess access)
: DeviceProperty(access), externalValue(externalValue)
{
}

uint32_t ExternalProperty::get_value() const
{
	if (access == PropertyAccess::ReadOnly || access == PropertyAccess::ReadWrite)
	{
		return *externalValue;
	}
	else
	{
		printf("ERR: property is WriteOnly\n");
		return 0;
	}
}

void ExternalProperty::set_value(uint32_t new_value)
{
	if (access == PropertyAccess::ReadWrite || access == PropertyAccess::WriteOnly)
	{
		*externalValue = new_value;
	}
	else
	{
		printf("ERR: property is ReadOnly\n");
	}
}

// FunctionProperty methods
FunctionProperty::FunctionProperty(PropGetter getter, PropSetter setter, PropertyAccess access)
: DeviceProperty(access), getter(getter), setter(setter)
{
}

uint32_t FunctionProperty::get_value() const
{
	if (access == PropertyAccess::ReadOnly || access == PropertyAccess::ReadWrite)
	{
		return getter ? getter() : 0;
	}
	else
	{
		printf("ERR: property is WriteOnly\n");
		return 0;
	}
}

void FunctionProperty::set_value(uint32_t new_value)
{
	if (access == PropertyAccess::ReadWrite || access == PropertyAccess::WriteOnly)
	{
		if (setter)
		{
			setter(new_value);
		}
	}
	else
	{
		printf("ERR: property is ReadOnly\n");
	}
}
