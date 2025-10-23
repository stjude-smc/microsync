Installation Guide
==================

This guide covers the installation and setup of the microsync project, including both the Python driver and firmware.

Python Driver Installation
--------------------------

Prerequisites
^^^^^^^^^^^^^

* Python 3.7 or higher
* pip package manager
* Serial port access (for device communication)

Install Dependencies
^^^^^^^^^^^^^^^^^^^^

Install the required Python packages:

.. code-block:: bash

   pip install pyserial

Install the microsync Driver
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Option 1: Copy the Python directory**

.. code-block:: bash

   # Clone or download the repository
   git clone https://github.com/stjude-smc/microsync.git
cd microsync
   
   # Copy the python directory to your project
   cp -r python/ /path/to/your/project/
   
   # Or add to your Python path
   export PYTHONPATH="${PYTHONPATH}:/path/to/microsync/python"

**Option 2: Install as a package (recommended for development)**

.. code-block:: bash

   # From the project root directory
   pip install -e .

Verify Installation
^^^^^^^^^^^^^^^^^^^

Test that the driver can be imported:

.. code-block:: python

   from microsync import SyncDevice
   print("Installation successful!")

Firmware Installation
---------------------

Prerequisites
^^^^^^^^^^^^^

* Microchip Studio (free download from Microchip)
* Arduino Due board
* USB cable
* Atmel ICE debugger (optional, for debugging)

Build the Firmware
^^^^^^^^^^^^^^^^^^

1. **Open the project in Microchip Studio:**

   .. code-block:: bash

      # Open the solution file
      microsync.atsln

2. **Configure build settings:**

   - Set build target to "Release"
   - Ensure all dependencies are resolved

3. **Build the project:**

   - Press F7 or use Build → Build Solution
   - Verify successful compilation

Firmware Upload
^^^^^^^^^^^^^^

Upload `microsync-<x.y.z>.bin` to your Arduino Due using BOSSA or Atmel-ICE with Microchip Studio.

**Method 1: Using BOSSA (Recommended - No Extra Hardware Required)**

1. Download BOSSA from https://github.com/shumatech/BOSSA/releases (pick the right binary for your OS)
2. Connect Due to your computer, use the USB port next to the power jack
3. Find newly created Arduino Due COM port (e.g. in the Device manager)
4. On your Due, press and hold **Erase** button for at least 0.5 seconds. This will wipe the current firmware and the microcontroller will enter the programming mode

**Upload via BOSSA GUI:**

1. Run BOSSA GUI
2. Select the correct COM port
3. Select `microsync-<x.y.z>.bin` file
4. **Important**: Check the "Boot from Flash" option (this sets GPNVM0=1)
5. Click "Write"

**Upload via command line:**

1. Put `bossac.exe` (or `bossac` on Mac/Linux) and `microsync-<x.y.z>.bin` in the same folder
2. Open a terminal in that folder and run (replace `<COM-PORT>` with the actual COM port of your Due):

   .. code-block:: sh

      bossac.exe -e -w -v -b microsync-<x.y.z>.bin -p <COM-PORT>

**Method 2: Using Microchip Studio with Atmel-ICE Debugger**

1. Connect Atmel-ICE SAM connector to JTAG header on your Due
2. Connect Atmel-ICE to your computer
3. Power up your Due with a USB cable
4. Open Microchip Studio
5. Open the Device Programming dialog (Ctrl+Shift+P)
6. Select Atmel-ICE tool, `ATSAM3X8E` device, JTAG interface, click "Apply"
7. Go to "Memory" tab, select `microsync-{version}.bin` file, click "Program"

Hardware Setup
--------------

Required Connections
^^^^^^^^^^^^^^^^^^^^

* **USB Connection:** Connect Arduino Due to host computer
* **Laser Shutters:** D8 (Cy2), D9 (Cy3), D10 (Cy5), D11 (Cy7) - configurable in ``globals.h``
* **Camera Trigger:** D7 - configurable in ``globals.h``
* **Interlock Circuit:** Connect between D12 (input) and D13 (output)

Power Supply
^^^^^^^^^^^^

The device is powered through the USB connection. No external power supply is required.

Driver Installation (Windows)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Download Arduino drivers from `arduino.cc <https://www.arduino.cc/en/software>`_
2. Install the drivers when prompted
3. The device will appear as "Arduino Due" in Device Manager

Verification
------------

Test the Complete Setup
^^^^^^^^^^^^^^^^^^^^^^^

1. **Connect the device:**

   .. code-block:: python

      from microsync import SyncDevice
      
      # Connect to device (replace COM4 with your port)
      sd = SyncDevice("COM4")
      print(f"Connected to device version: {sd.version}")

2. **Test basic functionality:**

   .. code-block:: python

      # Test event scheduling
      sd.pos_pulse("D8", 1000, N=5, interval=10000)  # Pulse on D8 (Cy2 laser)
      sd.go()
      
      # Check status
      print(sd.get_status())

3. **Verify communication:**

   .. code-block:: python

      # Test property access
      print(f"System timer running: {sd.running}")
      print(f"Number of events: {sd.N_events}")

Troubleshooting
---------------

Common Issues
^^^^^^^^^^^^^

**Connection Error:**
- Verify correct COM port
- Check USB cable connection
- Ensure drivers are installed

**Version Mismatch:**
- Update firmware to match Python driver version
- Check version compatibility

**Permission Errors:**
- Run as administrator (Windows)
- Check serial port permissions (Linux/Mac)

**Build Errors:**
- Verify Microchip Studio installation
- Check ASF (Atmel Software Framework) installation
- Ensure all dependencies are resolved

Getting Help
^^^^^^^^^^^^

* Check the README for troubleshooting tips
* Review the README for hardware documentation
* Open an issue on `GitHub <https://github.com/stjude-smc/microsync>`_

Next Steps
----------

After successful installation:

1. Read the :doc:`quickstart` guide
2. Explore the :doc:`api/index` documentation
3. Try the examples in the Jupyter notebook
4. Review the README for hardware setup 