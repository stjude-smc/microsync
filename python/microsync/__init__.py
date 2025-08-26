"""
Microsync package for 32-bit microscope synchronization device.

This package provides a Python driver for controlling and synchronizing
microscope components including lasers, cameras, and other timing-critical devices.
"""

from .microsync import SyncDevice
from .event_visualizer import EventVisualizer
from .constants import *
from .rev_pin_map import rev_pin_map
from .__version__ import __version__

__all__ = [
    'SyncDevice',
    'EventVisualizer', 
    'rev_pin_map',
    '__version__',
    # Constants
    'ms',
    'MHz', 
    'UNIFORM_TIME_DELAY'
]
