Firmware Build and Deployment
=============================

Building the Firmware
---------------------

Prerequisites
^^^^^^^^^^^^^

- **Microchip Studio** (free download from Microchip)
- **Arduino Due board**
- **micro-USB cable**
- **Atmel ICE debugger** (optional, for debugging)

Project Structure
^^^^^^^^^^^^^^^^^

.. code-block:: text

   microsync/
   ├── main.cpp                # Main application entry point
   ├── src/
   │   ├── globals.h           # Global definitions and constants
   │   ├── events.h/cpp        # Event system implementation
   │   ├── uart_comm.h/cpp     # UART communication
   │   ├── interlock.h/cpp     # Laser safety interlock
   │   ├── pins.h/cpp          # Pin management
   │   ├── props.h/cpp         # System properties
   │   └── ASF/                # Atmel Software Framework
   └── microsync.atsln         # Microchip Studio solution

Build Configuration
^^^^^^^^^^^^^^^^^^^

**Debug Configuration:**

- Full debug symbols, you can set breakpoints in the code and step through the code running on the board.
- Optimization disabled
- Development and testing

**Release Configuration:**

- Optimized for performance (-O2)
- Minimal debug information, no breakpoints can be set.
- Production deployment
- Reduced memory footprint

Build Steps
^^^^^^^^^^^

1. **Open** `microsync.atsln` in Microchip Studio.
2. **Select** Debug or Release config (target: Arduino Due).
3. **Build** (F7).  
4. **Check** for `microsync.bin` in Debug/ or Release/ folder.

Upload Methods
--------------

See the :doc:`../installation#firmware-upload` section in the installation guide.

Troubleshooting
---------------

Common Issues
^^^^^^^^^^^^^

**Build Errors:**

- Check ASF framework installation
- Verify include paths
- Ensure all source files are included

**Upload Failures:**

- Check USB connection
- Verify COM port settings
- Ensure Arduino Due is in programming mode

**Runtime Issues:**

- Check power supply
- Verify pin connections
- Monitor UART output for errors

Debugging
---------

Debug Features
^^^^^^^^^^^^^^

- **Breakpoints:** Set in Microchip Studio
- **Variable Watch:** Real-time value inspection
- **Call Stack:** Function call history
- **Memory Inspection:** RAM and register values

Note that pausing the program will not stop the running system timers, and you're likely to miss scheduled events.

Version Management
------------------

Version Information
^^^^^^^^^^^^^^^^^^^

The firmware version is defined in `globals.h`:

.. code-block:: cpp

   #define VERSION "2.4.0"

Version Compatibility
^^^^^^^^^^^^^^^^^^^^^

- **Python Driver**: Must match major and minor firmware version
- **Protocol**: Backward compatible within major versions
- **Features**: New features require updates to Python driver
