Welcome to microsync documentation!
==========================================

**Version:** |version|  
**Author:** Roman Kiselev  
**License:** Apache 2.0

A high-precision synchronization device for advanced microscope control, based on a 32-bit ARM microcontroller (Arduino Due).

`View on GitHub <https://github.com/stjude-smc/microsync>`_

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api/index
   cpp/architecture
   cpp/firmware
   cpp_api/library_root

Overview
--------

This project provides firmware and a Python driver for a high-precision synchronization device designed for advanced microscope control. The device enables precise timing and coordination of lasers, shutters, cameras, and other peripherals with microsecond precision.

Key Features
^^^^^^^^^^^^

* **Microsecond-precision event scheduling** with priority queue system
* **Laser shutter and interlock safety logic**
* **Advanced acquisition modes** (continuous, stroboscopic, ALEX)
* **Comprehensive Python API** with logging and context management
* **Event-driven architecture** supporting up to 450 scheduled events
* **Safety interlocks** for laser protection

Hardware Platform
^^^^^^^^^^^^^^^^^

* **Microcontroller:** Arduino Due (SAM3X8E ARM Cortex-M3)
* **Logic Levels:** 3.3V CMOS
* **Communication:** UART at 115,200 baud
* **Key Pins:** Laser shutters (D8-D11), Camera trigger (D7), Interlock (D12/D13)

Python API
^^^^^^^^^^

The Python driver provides a high-level interface for controlling the device:

.. code-block:: python

   from microsync import SyncDevice
   
   # Connect to device
   sd = SyncDevice("COM4")
   
   # Schedule events
   sd.pos_pulse("D8", 1000, N=10, interval=50000)  # Pulse on D8 (Cy2 laser)
   sd.go()

For detailed API documentation, see :doc:`api/index`.

Installation
^^^^^^^^^^^^

.. code-block:: bash

   pip install pyserial
   # Copy python/ directory to your project

For complete installation instructions, see :doc:`installation`.

Quick Start
^^^^^^^^^^^

1. Connect laser shutters and cameras to the Arduino Due pins. Use LED during testing.
1. Connect Arduino Due via USB
2. Install Python dependencies
3. Import and use the SyncDevice class
4. Schedule events and start acquisition

See :doc:`quickstart` for a step-by-step guide.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _GitHub: https://github.com/stjude-smc/microsync 