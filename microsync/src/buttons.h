/**
 * @file buttons.h
 * @brief Button input on D36-D38
 */

#pragma once

void init_buttons(void);

/** Call from main loop to process any pending button press; re-enables interrupts after handling. */
void process_button_events(void);
