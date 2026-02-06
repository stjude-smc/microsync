"""
Microsync package for 32-bit microscope synchronization device.

This package provides a Python driver for controlling and synchronizing
microscope components including lasers, cameras, and other timing-critical devices.
"""

from .microsync import SyncDevice, Event, props
from .tektronix import TDS2004
from .event_visualizer import EventVisualizer, plot_event_file
from .constants import *
from .rev_pin_map import rev_pin_map
from .__version__ import __version__

__all__ = [
    'SyncDevice',
    'EventVisualizer',
    'rev_pin_map',
    'props',
    '__version__',
    'main',
    # Constants
    'ms',
    'MHz',
    'UNIFORM_TIME_DELAY',
]


def main():
    """CLI entry point (e.g. `microsync` command after pip install)."""
    print(f"microsync {__version__}")
    print("Use as a library: from microsync import SyncDevice")
