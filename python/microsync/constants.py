"""
Constants module for `microsync` Python driver.

This module defines fundamental constants used throughout the microsync
Python driver, including time units, frequency units, and device-specific
configuration values.

Constants:
    ms: Time unit for milliseconds (0.001 seconds)
    us: Time unit for microseconds (0.001 milliseconds)
    kHz: Frequency unit for kilohertz (1000 Hz)
    MHz: Frequency unit for megahertz (1000 kHz)
    UNIFORM_TIME_DELAY: Default uniform time delay in microseconds
    BAUDRATE: UART communication baud rate
"""

# Time units for convenient conversion
ms = 0.001
"""Millisecond time unit (0.001 seconds)."""

us = 0.001 * ms
"""Microsecond time unit (0.001 milliseconds)."""

# Frequency units for convenient conversion
kHz = 1000
"""Kilohertz frequency unit (1000 Hz)."""

MHz = 1000*kHz
"""Megahertz frequency unit (1000 kHz)."""

# Device-specific constants
UNIFORM_TIME_DELAY = 500  # us
"""Default uniform time delay in microseconds for event scheduling."""

BAUDRATE = 115200
"""UART communication baud rate for device communication."""
