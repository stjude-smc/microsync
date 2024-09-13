/*
 * sd_pin_map.c
 *
 * Created: 9/12/2024 4:37:39 PM
 *  Author: rkiselev
 */ 

#include "sd_pin_map.h"

// Convert pin name (e.g., "D13" or "A0") to SAM3X I/O port pin ID
uint32_t pin_name_to_ioport_id(const uint8_t *pin_name) {
	//size_t map_size = sizeof(pin_map) / sizeof(pin_map[0]);
	size_t map_size = 80;

	// Iterate through the pin map to find the matching pin name
	for (size_t i = 0; i < map_size; i++) {
		if (strncasecmp((const char*) pin_name, pin_map[i].pin_name, 3) == 0) {
			// Return the PIO pin index
			return pin_map[i].pin_idx;
		}
	}

	// Return 0 if pin name is not found
	return 0;
}

// Arduino Due pin mapping table (digital and analog pins)
const pin_map_t pin_map[] = {
	{"D0", PIO_PA8_IDX},     // Digital pin D0 -> PA8
	{"D1", PIO_PA9_IDX},
	{"D2", PIO_PB25_IDX},
	{"D3", PIO_PC28_IDX},
	{"D4", PIO_PA29_IDX},
	{"D5", PIO_PC25_IDX},
	{"D6", PIO_PC24_IDX},
	{"D7", PIO_PC23_IDX},
	{"D8", PIO_PC22_IDX},
	{"D9", PIO_PC21_IDX},
	{"D10", PIO_PA28_IDX},
	{"D11", PIO_PD7_IDX},
	{"D12", PIO_PD8_IDX},
	{"D13", PIO_PB27_IDX},
	{"D14", PIO_PD4_IDX},
	{"D15", PIO_PD5_IDX},
	{"D16", PIO_PA13_IDX},
	{"D17", PIO_PA12_IDX},
	{"D18", PIO_PA11_IDX},
	{"D19", PIO_PA10_IDX},
	{"D20", PIO_PB12_IDX},
	{"D21", PIO_PB13_IDX},
	{"D22", PIO_PB26_IDX},
	{"D23", PIO_PA14_IDX},
	{"D24", PIO_PA15_IDX},
	{"D25", PIO_PD0_IDX},
	{"D26", PIO_PD1_IDX},
	{"D27", PIO_PD2_IDX},
	{"D28", PIO_PD3_IDX},
	{"D29", PIO_PD6_IDX},
	{"D30", PIO_PD9_IDX},
	{"D31", PIO_PA7_IDX},
	{"D32", PIO_PD10_IDX},
	{"D33", PIO_PC1_IDX},
	{"D34", PIO_PC2_IDX},
	{"D35", PIO_PC3_IDX},
	{"D36", PIO_PC4_IDX},
	{"D37", PIO_PC5_IDX},
	{"D38", PIO_PC6_IDX},
	{"D39", PIO_PC7_IDX},
	{"D40", PIO_PC8_IDX},
	{"D41", PIO_PC9_IDX},
	{"D42", PIO_PA19_IDX},
	{"D43", PIO_PA20_IDX},
	{"D44", PIO_PC19_IDX},
	{"D45", PIO_PC18_IDX},
	{"D46", PIO_PC17_IDX},
	{"D47", PIO_PC16_IDX},
	{"D48", PIO_PC15_IDX},
	{"D49", PIO_PC14_IDX},
	{"D50", PIO_PC13_IDX},
	{"D51", PIO_PC12_IDX},
	{"D52", PIO_PB21_IDX},
	{"D53", PIO_PB14_IDX},
	{"D54", PIO_PA16_IDX},
	{"D55", PIO_PA24_IDX},
	{"D56", PIO_PA23_IDX},
	{"D57", PIO_PA22_IDX},
	{"D58", PIO_PA6_IDX},
	{"D59", PIO_PA4_IDX},
	{"D60", PIO_PA3_IDX},
	{"D61", PIO_PA2_IDX},
	{"D62", PIO_PB17_IDX},
	{"D63", PIO_PB18_IDX},
	{"D64", PIO_PB19_IDX},
	{"D65", PIO_PB20_IDX},
	{"D66", PIO_PB15_IDX},
	{"D67", PIO_PB16_IDX},

	{"A0", PIO_PA16_IDX},
	{"A1", PIO_PA24_IDX},
	{"A2", PIO_PA23_IDX},
	{"A3", PIO_PA22_IDX},
	{"A4", PIO_PA6_IDX},
	{"A5", PIO_PA4_IDX},
	{"A6", PIO_PA3_IDX},
	{"A7", PIO_PA2_IDX},
	{"A8", PIO_PB17_IDX},
	{"A9", PIO_PB18_IDX},
	{"A10", PIO_PB19_IDX},
	{"A11", PIO_PB20_IDX},
};
