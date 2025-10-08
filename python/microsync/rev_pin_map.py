"""
Reverse pin mapping for microsync Python driver.

This module provides a reverse mapping from internal pin IDs to human-readable
Arduino Due pin names. The mapping converts the device's internal pin numbering
system to the familiar Arduino pin names (D0-D65, A0-A15).

The reverse pin map is used for:
- Converting internal pin IDs to readable names in error messages
- Providing user-friendly pin identification in logs and debugging
- Maintaining compatibility with Arduino pin naming conventions

Note:
    This mapping is specific to the Arduino Due board and the SAM3X8E
    microcontroller pin configuration used in microsync.
"""

rev_pin_map = {
    # Digital pins (D0-D65)
    8: "D0",
    9: "D1",
    32+25: "D2",
    64+28: "D3",
    29: "D4",
    64+25: "D5",
    64+24: "D6",
    64+23: "D7",
    64+22: "D8",
    64+21: "D9",
    28: "D10",
    96+7: "D11",
    96+8: "D12",
    32+27: "D13",
    96+4: "D14",
    96+5: "D15",
    13: "D16",
    12: "D17",
    11: "D18",
    10: "D19",
    32+12: "D20",
    32+13: "D21",
    32+26: "D22",
    14: "D23",
    15: "D24",
    96+0: "D25",
    96+1: "D26",
    96+2: "D27",
    96+3: "D28",
    96+6: "D29",
    96+9: "D30",
    7: "D31",
    96+10: "D32",
    64+1: "D33",
    64+2: "D34",
    64+3: "D35",
    64+4: "D36",
    64+5: "D37",
    64+6: "D38",
    64+7: "D39",
    64+8: "D40",
    64+9: "D41",
    19: "D42",
    20: "D43",
    64+19: "D44",
    64+18: "D45",
    64+17: "D46",
    64+16: "D47",
    64+15: "D48",
    64+14: "D49",
    64+13: "D50",
    64+12: "D51",
    32+21: "D52",
    32+14: "D53",
    16: "D54",
    24: "D55",
    23: "D56",
    22: "D57",
    6: "D58",
    4: "D59",
    3: "D60",
    2: "D61",
    32+17: "D62",
    32+18: "D63",
    32+19: "D64",
    32+20: "D65",

    # Analog pins (A0-A15)
    16: "A0",
    24: "A1",
    23: "A2",
    22: "A3",
    6: "A4",
    4: "A5",
    3: "A6",
    2: "A7",
    32+17: "A8",
    32+18: "A9",
    32+19: "A10",
    32+20: "A11",
    32+15: "A12",
    32+16: "A13",
    1: "A14",
    0: "A15",
}
"""Reverse mapping from internal pin IDs to Arduino Due pin names.

This dictionary maps the device's internal pin IDs to human-readable
Arduino Due pin names. The mapping includes:
- Digital pins D0 through D65
- Analog pins A0 through A15

The internal pin IDs are based on the SAM3X8E microcontroller's
port and pin numbering system, while the Arduino names follow
the standard Arduino Due pinout convention.

Example:
    >>> rev_pin_map[8]
    'D0'
    >>> rev_pin_map[16]
    'A0'
"""
