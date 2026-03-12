"""
Microsync package for 32-bit microscope synchronization device.

This package provides a Python driver for controlling and synchronizing
microscope components including lasers, cameras, and other timing-critical devices.
"""

from .microsync import SyncDevice, Event, props
from .constants import *
from .rev_pin_map import rev_pin_map
from .__version__ import __version__

# Optional extras: Tektronix jitter testing and event visualization.
# These are imported lazily so that the base package works without
# heavy dependencies like numpy, pandas, or bokeh.
try:  # jitter / Tektronix support
    from .tektronix import TDS2004  # type: ignore[import]
except Exception:  # Missing optional dependencies
    TDS2004 = None  # type: ignore[assignment]

try:  # event visualization support
    from .event_visualizer import EventVisualizer, plot_event_file  # type: ignore[import]
except Exception:
    EventVisualizer = None  # type: ignore[assignment]
    plot_event_file = None  # type: ignore[assignment]

__all__ = [
    'SyncDevice',
    'rev_pin_map',
    'props',
    '__version__',
    'main',
    # Constants
    'ms',
    'MHz',
    'UNIFORM_TIME_DELAY',
]

if TDS2004 is not None:
    __all__.append('TDS2004')

if EventVisualizer is not None:
    __all__.extend(['EventVisualizer', 'plot_event_file'])


def main():
    """CLI entry point (e.g. `microsync` command after pip install)."""
    print(f"microsync {__version__}")
    print("Use as a library: from microsync import SyncDevice")
