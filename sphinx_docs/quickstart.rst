Quick Start Guide
=================

This guide will get you up and running with microsync in minutes. It covers the basic setup and common usage patterns.

Basic Setup
-----------

1. **Install the Python driver:**

   .. code-block:: bash

      pip install pyserial
      # Copy the python/ directory to your project

2. **Connect your Arduino Due:**

   .. code-block:: python

      from microsync import SyncDevice
      
      # Connect to device (replace COM4 with your port)
      sd = SyncDevice("COM4")
      print(f"Connected! Firmware version: {sd.version}")

Basic Event Scheduling
----------------------

**Simple Pulse Generation:**

.. code-block:: python

   # Generate a 1ms pulse on pin A0
   sd.pos_pulse("A0", 1000)
   sd.go()

**Repeating Events:**

.. code-block:: python

   # Generate 10 pulses, 1ms each, every 50ms
   sd.pos_pulse("A0", 1000, N=10, interval=50000)
   sd.go()

**Multiple Events:**

.. code-block:: python

   # Schedule multiple events
   sd.pos_pulse("A0", 1000, ts=0)      # At t=0
   sd.pos_pulse("A1", 1000, ts=5000)   # At t=5ms
   sd.pos_pulse("A2", 1000, ts=10000)  # At t=10ms
   sd.go()

**Using Context Manager for Precise Timing:**

.. code-block:: python

   # Batch commands for precise timing
   with sd as dev:
       dev.pos_pulse("A0", 1000, ts=0)
       dev.pos_pulse("A1", 1000, ts=5000)
       dev.pos_pulse("A2", 1000, ts=10000)
   # All commands sent together

Laser Control
--------------

**Basic Laser Shutter Control:**

.. code-block:: python

   # Open all laser shutters
   sd.open_shutters()
   
   # Close specific shutters (Cy2 and Cy5)
   sd.close_shutters(1 | 4)
   
   # Select which lasers are enabled
   sd.selected_lasers = 0b0110  # Enable Cy3 and Cy5

**Laser Interlock:**

.. code-block:: python

   # Check interlock status
   print(f"Interlock enabled: {sd.interlock_enabled}")
   
   # Disable interlock (for testing only)
   sd.interlock_enabled = False

Acquisition Modes
-----------------

**Continuous Imaging:**

.. code-block:: python

   # Configure timing
   sd.shutter_delay_us = 1300
   sd.cam_readout_us = 14000
   
   # Start continuous acquisition
   sd.start_continuous_acq(exp_time=200000, N_frames=15)
   sd.go()

**Stroboscopic Imaging:**

.. code-block:: python

   # Start stroboscopic acquisition
   sd.start_stroboscopic_acq(exp_time=200000, N_frames=15)
   sd.go()

**ALEX (Multi-spectral) Imaging:**

.. code-block:: python

   # Select lasers for ALEX
   sd.selected_lasers = 0b1111  # All lasers
   
   # Start ALEX acquisition
   sd.start_ALEX_acq(exp_time=50000, N_bursts=9)
   sd.go()

System Control
--------------

**Start/Stop Control:**

.. code-block:: python

   # Start processing events
   sd.go()
   
   # Stop processing (events remain in queue)
   sd.stop()
   
   # Resume processing
   sd.go()

**Event Management:**

.. code-block:: python

   # Clear all scheduled events
   sd.clear()
   
   # Check how many events are scheduled
   print(f"Events in queue: {sd.N_events}")
   
   # Get list of scheduled events
   events = sd.get_events("us")
   for event in events:
       print(f"{event.func} at {event.ts} {event.unit}")

**System Status:**

.. code-block:: python

   # Get detailed status
   print(sd.get_status())
   
   # Check if system is running
   print(f"System running: {sd.running}")
   
   # Get current system time
   print(f"System time: {sd.sys_time_s:.3f} seconds")

Configuration
-------------

**Timing Parameters:**

.. code-block:: python

   # Set default pulse duration
   sd.pulse_duration_us = 800
   
   # Set camera readout time
   sd.cam_readout_us = 14000
   
   # Set shutter delay
   sd.shutter_delay_us = 1300

**Logging:**

.. code-block:: python

   # Enable communication logging
   sd = SyncDevice("COM4", log_file="sync.log")
   
   # Or print to terminal
   sd = SyncDevice("COM4", log_file="print")

Common Patterns
---------------

**Timelapse Acquisition:**

.. code-block:: python

   # Stroboscopic with timelapse
   sd.start_stroboscopic_acq(
       exp_time=200000, 
       N_frames=5, 
       frame_period=1500000  # 1.5s between frames
   )
   sd.go()

**Multi-channel Control:**

.. code-block:: python

   # Control multiple pins simultaneously
   with sd as dev:
       dev.pos_pulse("D8", 1000, ts=0)      # Cy2 laser
       dev.pos_pulse("D9", 1000, ts=1000)   # Cy3 laser
       dev.pos_pulse("D10", 1000, ts=2000)  # Cy5 laser
       dev.pos_pulse("D7", 100, ts=500)     # Camera trigger

**Error Handling:**

.. code-block:: python

   try:
       sd = SyncDevice("COM4")
       sd.pos_pulse("A0", 1000)
       sd.go()
   except Exception as e:
       print(f"Error: {e}")
       # Handle error appropriately

Next Steps
----------

Now that you have the basics:

1. **Explore the API:** See :doc:`api/index` for complete documentation
2. **Try examples:** Check the Jupyter notebook for more complex scenarios
3. **Learn about hardware:** Review the README for connection details
4. **Understand firmware:** See the source code for technical details

**Need help?** Open an issue on GitHub or check the README. 