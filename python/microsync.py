from __version__ import __version__
from constants import ms, MHz, UNIFORM_TIME_DELAY
from ctypes import c_int32
from ctypes import c_uint16
from ctypes import c_uint32
from ctypes import c_uint8
from enum import Enum
from rev_pin_map import rev_pin_map
from serial import Serial, SerialException
import ctypes
import datetime
import gc
import re
import time

####################################################################
#        INTEGER CONVERSION FUNCTIONS BETWEEN C AND PYTHON
####################################################################

def cu8(value):
    assert value < 2**8, "value exceeds 8 bit"
    return c_uint8(value)

def cu16(value):
    assert value < 2**16, "value exceeds 16 bit"
    return c_uint16(value)

def cu32(value):
    assert value < 2**32, "value exceeds 32 bit"
    return c_uint32(value)

def c32(value):
    assert -(2**31) < value < 2**31, "value exceeds 32 bit"
    return c_int32(value)

class UInt32(ctypes.LittleEndianStructure):
    _fields_ = [("value", ctypes.c_uint32)]

class UInt64(ctypes.LittleEndianStructure):
    _fields_ = [("value", ctypes.c_uint64)]

def uint32_to_py(buf: bytearray):
    return ctypes.cast(buf, ctypes.POINTER(UInt32)).contents.value

def uint64_to_py(buf: bytearray):
    return ctypes.cast(buf, ctypes.POINTER(UInt64)).contents.value



####################################################################
#        HELPER FUNCTIONS
####################################################################
def _compare_versions(v1, v2):
    return {
        k: a == b
        for k, a, b in zip(["major", "minor", "patch"], v1.split("."), v2.split("."))
    }

def pad(data: bytearray, length=24):
    """
    Pad a bytearray to a given length with zeros. Used to create data packets of fixed length.
    """
    return bytearray(data + bytearray([0] * (length - len(data))))

def us2cts(us, prescaler=0):
    """
    Convert microseconds to clock ticks.
    """
    if prescaler == 0:
        prescaler = get_prescaler()

    return us * 84_000_000 // prescaler // 1_000_000


def cts2us(cts, prescaler=0):
    """
    Convert clock ticks to microseconds.
    """
    if prescaler == 0:
        prescaler = get_prescaler()

    return cts * 1_000_000 * prescaler // 84_000_000

def close_lost_serial_port(port_name):
    """
    Close a serial port that was lost (e.g. due to a crash of another instance of the driver).
    It looks through all objects of the garbage collector until it finds the serial port with
    the given name and closes it.
    """
    for obj in gc.get_objects():
        if isinstance(obj, Serial):
            if obj.port == port_name and obj.is_open:
                obj.close()
                return True
    print(f"No open port found with name {port_name}")
    return False



####################################################################
#        SYNC DEVICE PROPERTIES (see props.h)
####################################################################

class props(Enum):
    """
    Enum class for the properties of the sync device.
    See corresponding enum in props.h
    """
    ro_VERSION = 0                #: Device version number (read-only)
    ro_SYS_TIMER_STATUS = 1       #: System timer running status (read-only)
    ro_SYS_TIMER_VALUE = 2        #: Current system timer value (read-only)
    ro_SYS_TIMER_OVF_COUNT = 3    #: System timer overflow count (read-only)
    ro_SYS_TIME_s = 4             #: Current system time in seconds (read-only)
    ro_SYS_TIMER_PRESCALER = 5    #: System timer prescaler value (read-only)
    rw_DFLT_PULSE_DURATION_us = 6 #: Default pulse duration in microseconds (read-write)
    ro_WATCHDOG_TIMEOUT_ms = 7    #: Watchdog timeout in milliseconds (read-only)
    ro_N_EVENTS = 8               #: Number of events in queue (read-only)
    rw_INTLCK_ENABLED = 9         #: Laser interlock enabled state (read-write)
    # pTIRF extension
    rw_SELECTED_LASERS = 10       #: Selected laser mask (read-write)
    wo_OPEN_SHUTTERS = 11         #: Open all shutters (write-only)
    wo_CLOSE_SHUTTERS = 12        #: Close all shutters (write-only)
    rw_SHUTTER_DELAY_us = 13      #: Shutter delay in microseconds (read-write)
    rw_CAM_READOUT_us = 14        #: Camera readout time in microseconds (read-write)

####################################################################
#        LOGGING SERIAL PORT CLASS
####################################################################
class SyncDeviceError(ValueError):
    """
    Exception class for errors returned by the sync device.
    """
    def __init__(self, reply):
        super().__init__(reply)

class LoggingSerial(Serial):
    """
    Serial port class with logging functionality. 
    If log_file is set, the data sent to and received from the serial port is logged to the file.
    If log_file is set to "print", the data is printed to the console.
    If log_file is not set, no logging is performed.
    """
    def __init__(self, *args, log_file=None, **kwargs):
        super().__init__(*args, **kwargs)
        if log_file == "print":
            self.log_to_stdout = True
            self.log_file = None
        else:
            self.log_to_stdout = False
            self.log_file = log_file if log_file else None

    def _format_data(self, data):
        # Convert each byte to ASCII or hex notation
        formatted_data = ''.join(
            chr(byte) if 32 <= byte <= 126 else f'\\x{byte:02X}' 
            for byte in data
        )
        return formatted_data

    def write(self, data):
        """
        Write data to the serial port.
        If logging is enabled, the data is logged to the file or printed to the
        console in addition to being sent to the device. The logged data includes a timestamp.
        """
        if self.log_file or self.log_to_stdout:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            log_entry = (f"{timestamp} TX: {self._format_data(data)}\n")
            if self.log_to_stdout:
                print(log_entry, end='')
            else:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
        super().write(data)

    def readline(self, size=None):
        """
        Read a line from the serial port.
        If logging is enabled, the data is logged to the file or printed to the
        console in addition to being returned. The logged data includes a timestamp.
        """
        data = super().readline(size)
        if data and (self.log_file or self.log_to_stdout):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            log_entry = f"{timestamp} RX: {self._format_data(data)}\n"
            if self.log_to_stdout:
                print(log_entry, end='')
            else:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
        return data

    def readall(self):
        """
        Read all data from the serial port.
        If logging is enabled, the data is logged to the file or printed to the
        console in addition to being returned. The logged data includes a timestamp.
        """
        data = super().readall()
        if data and (self.log_file or self.log_to_stdout):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            log_entry = f"{timestamp} RX: {self._format_data(data)}\n"
            if self.log_to_stdout:
                print(log_entry, end='')
            else:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
        return data

    def close(self):
        """
        Close the serial port.
        """
        super().close()

class Port(LoggingSerial):
    """
    Serial port class for the sync device.
    It is a subclass of LoggingSerial, and adds a context manager for batch command transmission.
    """
    def __enter__(self):
        """
        Enter context manager for batch command transmission.
        """
        self.reset_input_buffer()
        return self

    def __exit__(self, *args, **kwargs):
        """
        Exit context manager and transmit batched commands.
        """
        reply = self.readline().strip().decode()
        if reply.startswith("ERR"):
            raise SyncDeviceError(reply)



####################################################################
#        EVENT FROM DEVICE PRIORITY QUEUE
####################################################################

class Event:
    """
    Represents a scheduled event in the device's priority queue.
    
    This class contains all the information needed to execute an event,
    including the function to call, its arguments, timing, and repetition
    parameters.
    
    Attributes:
        func (str): Function name to execute
        arg1: First argument (usually pin number)
        arg2: Second argument (usually level or duration)
        ts (int): Timestamp when to execute the event (in specified units)
        N (int): Number of remaining event repetitions
        intvl (int): Interval between event repetitions
        unit (str): Time unit ("cts", "us", or "ms")
    """
    
    def __init__(self, c_struct_data):
        """
        Create an Event from raw C structure data.
        
        Args:
            c_struct_data (bytes): 28-byte C structure data from device
        """
        self.func = uint32_to_py(c_struct_data[0:4])
        self.arg1 = uint32_to_py(c_struct_data[4:8])
        self.arg2 = uint32_to_py(c_struct_data[8:12])
        self.ts = uint64_to_py(c_struct_data[12:20])
        self.N = uint32_to_py(c_struct_data[20:24])
        self.intvl = uint32_to_py(c_struct_data[24:28])
        self.unit = "cts"

    def __repr__(self):
        """
        Return a string representation of the sync device event.
        """
        f = self.func
        arg1 = self.arg1
        if f in ["SET_PIN", "TGL_PIN"]:
            arg1 = rev_pin_map[arg1]
        return (f"{f}({arg1:<3}, {self.arg2:<3}) at " 
              + f"t={self.ts:>11}{self.unit}. Call "
              + f"{self.N:>6} times every {self.intvl:>10} {self.unit}")

    def map_func(self, func_map):
        """
        Map the function address to the corresponding function name.
        This is used to convert the function address returned by the device
        to the corresponding function name for pretty printing of the event table.
        """
        self.func = func_map[str(self.func)]
    
    def expand_repeating_events(self):
        """
        Expand repeating events into their full sequence.
        
        Returns:
            list: List of Event objects representing all instances of repeating events
        """
        if self.N > 1 and self.intvl > 0:
            # Repeating event - create N instances
            expanded_events = []
            for i in range(self.N):
                expanded_event = type('Event', (), {
                    'ts': self.ts + i * self.intvl,
                    'arg1': self.arg1,
                    'arg2': self.arg2,
                    'func': self.func,
                    'N': 1,
                    'intvl': 0
                })()
                expanded_events.append(expanded_event)
            return expanded_events
        else:
            # Single event
            return [self]



####################################################################
#        SYNC DEVICE INTERFACE CLASS
####################################################################

class SyncDevice(object):
    """
    Python interface for 32-bit microscope synchronization device.
    
    This class provides a high-level API for controlling the Arduino Due-based
    synchronization device. It handles communication, event scheduling, and
    provides convenient methods for common microscope control tasks.
    
    The device supports microsecond-precision event scheduling with a priority
    queue system, laser shutter control, and various acquisition modes.
    
    Attributes:
        com: Serial communication interface
        func_map: Mapping of function addresses from device
        _pending_tx_: Buffer for context manager commands
        _in_context: Context manager state flag

    Note:
        Opening the port and connecting to the sync device resets the device.

    Example:
        >>> sd = SyncDevice("COM4")
        >>> sd.pos_pulse("A0", 1000, N=10, interval=50000)
        >>> sd.go()
    """
    
    def __init__(self, port, log_file=None):
        """
        Initialize connection to the sync device and reset it.
        
        Args:
            port (str): Serial port name (e.g., "COM4", "/dev/ttyUSB0")
            log_file (str, optional): Logging configuration:
                - None: No logging
                - "print": Print to terminal
                - filename: Save to file
        
        Raises:
            ConnectionError: If device connection fails
            RuntimeWarning: If firmware/driver version mismatch
        
        Example:
            >>> sd = SyncDevice("COM4", log_file="sync.log")
            >>> sd = SyncDevice("/dev/ttyUSB0", log_file="print")
        """
        self._pending_tx_ = bytearray()
        self._in_context = False

        try:
            self.com = Port(port, baudrate=115200, log_file=log_file)
        except SerialException as e:
            close_lost_serial_port(port)
            print(f"{port} is in use. Closing and re-opening...")
            self.com = Port(port, baudrate=115200, log_file=log_file)

        # Opening of the serial port resets MCU, so we are going to wait for it to start up
        self.com.timeout = 1000 * ms
        msg = self.com.readline().strip().decode()
        self.com.timeout = 20 * ms
        time.sleep(0.025)

        # Ensure that firmware and driver have the same version
        msg_template = "Sync device is ready. Firmware version: "
        if msg.find(msg_template) != 0:
            raise ConnectionError(
                f"Could not connect to Arduino on port {port};\n"
                + f"Received message:\n{msg}\n"
                + f"Expected message:\n{msg_template + __version__}"
            )

        v = self.version
        self.driver_version = __version__
        version_match = _compare_versions(v, __version__)
        if not version_match["major"] or not version_match["minor"]:
            raise RuntimeWarning(
                f"Version mismatch: driver {__version__} != firmware {v}"
            )

        self.func_map = self.get_function_addr()


    def __enter__(self):
        """
        Enter context manager for batch command transmission.

        After entering the context manager, commands sent to the device are not transmitted immediately.
        Instead, they are queued and transmitted as a single batch when exiting the context manager.
        
        Example:
            >>> with sd as dev:
            ...     dev.pos_pulse("A0", 1000, ts=0)
            ...     dev.pos_pulse("A1", 1000, ts=5000)
        """
        self._in_context = True
        return self

    def __exit__(self, *args, **kwargs):
        """
        Exit context manager and transmit batched commands.
        
        All commands collected within the context manager are sent as a single
        data packet to ensure precise timing and eliminate host OS jitter.
        """
        self._in_context = False
        if(self._pending_tx_):
            self.com.write(self._pending_tx_)
        self._pending_tx_ = bytearray()

    def __del__(self):
        """
        Close the serial port when the object is deleted.
        """
        self.com.close()

    def __repr__(self):
        """
        The string representation of the sync device is the status of the device.
        """
        return self.get_status()

    def write(self, cmd: str, arg1=0, arg2=0, ts=0, N=0, interval=0):
        """
        Send a command to the synchronization device.
        If the device is in a context manager, the command is queued and transmitted as a single batch when exiting the context manager.
        If the device is not in a context manager, the command is transmitted immediately.
        
        Args:
            cmd (str): 3-character command code
            arg1: First argument (can be string or integer)
            arg2 (int): Second argument
            ts (int): Timestamp (in microseconds)
            N (int): Number of event repetitions
            interval (int): Interval between event repetitions (in microseconds)
        
        Note:
            This is a low-level method. For most applications,
            use the high-level methods like pos_pulse(), tgl_pin(), etc.
        """
        self.com.reset_input_buffer()
        _command = pad(cmd.encode(), 4)
        if type(arg1) is str:
            arg1 = pad(arg1.encode(), 4)
        else:
            arg1 = bytearray(cu32(arg1))

        data = (pad(cmd.encode(), 4)
            + arg1
            + bytearray(cu32(arg2))
            + bytearray(cu32(ts))
            + bytearray(cu32(N))
            + bytearray(cu32(interval)))

        if self._in_context:
            self._pending_tx_ += data
            return

        self.com.write(data)

    def query(self, cmd: str, arg1=0, arg2=0, ts=0, N=0, interval=0):
        """
        Query the sync device - write a command and read the reply.
        """
        if self._in_context:
            raise RuntimeError("Can't run queries inside of a context manager")

        self.write(cmd, arg1, arg2, ts, N, interval)

        reply = self.com.readline().strip().decode()
        if reply.startswith("ERR"):
            raise SyncDeviceError(reply)
        return reply

    def set_pin(self, pin, level, ts=0, N=0, interval=0):
        """
        Set a pin to a specific logical level.
        Attempting to set a previously unused pin configures it as an output pin.

        Args:
            pin (str): Arduino Due pin name (e.g., "A0", "D13")
            level (int): Pin level (0=low, 1=high)
            ts (int): Timestamp (in microseconds, relative to current time)
            N (int): Number of event repetitions (0=infinite)
            interval (int): Interval between event repetitions (in microseconds)
        
        Example:
            >>> sd.set_pin("A0", 1, ts=1000)  # Set A0 high after 1ms
        """
        self.write("PIN", pin, level, ts, N, interval)

    def tgl_pin(self, pin, ts=0, N=0, interval=0):
        """
        Toggle a pin state.
        Attempting to toggle a previously unused pin configures it as an output pin.
        
        Args:
            pin (str): Arduino Due pin name (e.g., "A0", "D13")
            ts (int): Timestamp (in microseconds, relative to current time)
            N (int): Number of event repetitions (0=infinite)
            interval (int): Interval between event repetitions (in microseconds)
        
        Example:
            >>> sd.tgl_pin("D13", N=1000, interval=1000)  # Toggle D13 every 1ms
        """
        self.write("TGL", pin, 0, ts, N, interval)

    def pos_pulse(self, pin, duration=0, ts=0, N=0, interval=0):
        """
        Generate a positive pulse on a pin.
        Attempting to generate a pulse on a previously unused pin configures it as an output pin.
        
        Args:
            pin (str): Arduino Due pin name (e.g., "A0", "D13")
            duration (int): Pulse duration (in microseconds)
            ts (int): Timestamp (in microseconds, relative to current time)
            N (int): Number of event repetitions (0=infinite)
            interval (int): Interval between event repetitions (in microseconds)
        
        Example:
            >>> sd.pos_pulse("A0", 1000, ts=5000, N=10, interval=50000)
        """
        self.write("PPL", pin, duration, ts, N, interval)

    def neg_pulse(self, pin, duration=0, ts=0, N=0, interval=0):
        """
        Generate a negative pulse on a pin.
        Attempting to generate a pulse on a previously unused pin configures it as an output pin.
        
        Args:
            pin (str): Arduino Due pin name (e.g., "A0", "D13")
            duration (int): Pulse duration (in microseconds)
            ts (int): Timestamp (in microseconds, relative to current time)
            N (int): Number of event repetitions (0=infinite)
            interval (int): Interval between event repetitions (in microseconds)
        
        Example:
            >>> sd.neg_pulse("A0", 1000, ts=5000, N=10, interval=50000)
        """
        self.write("NPL", pin, duration, ts, N, interval)

    def pulse_train(self, period, duration=0, ts=0, N=0, interval=0):
        """
        Generate a burst of pulses.
        
        Args:
            period (int): Period between pulses (in microseconds)
            duration (int): Duration of each pulse (in microseconds)
            ts (int): Timestamp (in microseconds, relative to current time)
            N (int): Number of event repetitions (0=infinite)
            interval (int): Interval between event repetitions (in microseconds)
        
        Example:
            >>> sd.pulse_train(1000, 100, ts=0, N=1000)  # 1000 pulses, 1kHz
        """
        self.write("BST", period, duration, ts, N, interval)

    def enable_pin(self, pin, ts=0, N=0, interval=0):
        """
        Enable a pin, setting it as active. The logical level of the pin is preserved.
        
        Args:
            pin (str): Arduino Due pin name (e.g., "A0", "D13")
            ts (int): Timestamp (in microseconds, relative to current time)
            N (int): Number of event repetitions (0=infinite)
            interval (int): Interval between event repetitions (in microseconds)
        
        Example:
            >>> sd.disable_pin("A0")  # Disable A0. It will stay low regardless of calls to set_pin()
            >>> sd.set_pin("A0", 1)   # Set A0 high. It will still stay low as the pin is disabled
            >>> sd.enable_pin("A0", ts=1000)  # Enable A0 after 1ms. It will restore logical high level set by the previous call to set_pin()
        """
        self.write("ENP", pin, 0, ts, N, interval)

    def disable_pin(self, pin, ts=0, N=0, interval=0):
        """
        Disable a pin output. The previous logical value of the pin is preserved.
        
        Args:
            pin (str): Arduino Due pin name (e.g., "A0", "D13")
            ts (int): Timestamp (in microseconds, relative to current time)
            N (int): Number of event repetitions (0=infinite)
            interval (int): Interval between event repetitions (in microseconds)
        
        Example:
            >>> sd.disable_pin("A0", ts=1000)  # Disable A0 after 1ms
        """
        self.write("DSP", pin, 0, ts, N, interval)

    def go(self):
        """
        Start the system timer and begin processing scheduled events.
        
        This method starts the hardware timer that processes the event queue.
        All scheduled events will be called exactly at their specified timestamps.
        
        If more than one event is scheduled at the same time, their order of execution is undefined.
        
        Example:
            >>> sd.pos_pulse("A0", 1000, ts=1000)  # Sends positive pulse 1ms after go() is called
            >>> sd.go()  # Start processing events
        """
        self.write("GO!")

    def stop(self):
        """
        Stop the sync device system timer and halt event processing.
        
        This method stops and resets the hardware timer, and deletes the event queue.
        
        Example:
            >>> sd.stop()  # Pause event processing
            >>> # schedule some events
            >>> sd.go()    # Start processing events (from t=0)
        """
        self.write("STP")

    def clear(self):
        """
        Clear all scheduled events from the event queue.
        
        This method removes all pending events from the event queue.
        The system timer is not affected and keeps running - use
        stop() to halt processing and reset the timer.
        
        Example:
            >>> sd.clear()  # Remove all scheduled events
        """
        self.write("CLR")

    def reset(self):
        """
        Reset the sync device and clear all events.
        
        This method performs a soft reset of the device, clearing all events
        and resetting system parameters to their default values. A "soft reset"
        triggers a processor reset via software by writing a key and command to the
        Reset Controller (RSTC), which restarts the CPU without cycling power or
        affecting external peripherals.

        Note:
            This operation will immediately stop the running hardware system timer,
            clear the event queue, and restart the device firmware. All scheduled
            events and timer state will be lost, and the device will reboot to its
            initial state, and send a startup message, indicating the firmware version.
        
        Example:
            >>> sd.reset()  # Reset device to default state
        """
        self.write("RST")

    def get_status(self):
        """
        Get detailed system status information.

        The status report includes the following information:
        - Firmware version
        - System status header
        - Number of events in the event queue
        - System timer status (RUNNING or STOPPED)
        - System time in seconds

        Example:
            >>> status = sd.get_status()
            >>> print(status)
        """
        self.write("STA")
        return self.com.readall().decode()

    def get_property(self, prop):
        """
        Get a device property value; if the property is write-only, it will return an error.
        
        Args:
            prop: Property enum or integer ID, see props.h for available properties
        
        Returns:
            str: Property value as string
        
        Example:
            >>> version = sd.get_property(props.ro_VERSION)
        """
        if isinstance(prop, Enum):
            prop = prop.value
        return self.query("GET", prop)

    def set_property(self, prop, value):
        """
        Set a device property value; if the property is read-only, it will return an error.
        
        Args:
            prop: Property enum or integer ID, see props.h for available properties
            value: New property value
        
        Example:
            >>> sd.set_property(props.rw_DFLT_PULSE_DURATION_us, 1000)
        """
        if isinstance(prop, Enum):
            prop = prop.value
        return self.write("SET", prop, value)

    @property
    def version(self):
        """
        Get the firmware version. The version is a string of the form "X.Y.Z",
        where X=major, Y=minor, and Z=patch. The major and minor version number
        of the firmware and the driver must match.

        Returns:
            str: Firmware version string (e.g., "2.4.0")
        """
        return self.get_property(props.ro_VERSION)

    @property
    def running(self):
        """
        Check whether the sync device system timer is running.
        
        Returns:
            bool: True if system timer is active, False otherwise
        """
        return self.get_property(props.ro_SYS_TIMER_STATUS) != '0'

    @property
    def sys_time_cts(self):
        """
        Get current sync device system time in counter ticks.
        
        Returns:
            int: 64-bit system time in counter ticks
        """
        cv = int(self.get_property(props.ro_SYS_TIMER_VALUE))
        ovf = int(self.get_property(props.ro_SYS_TIMER_OVF_COUNT))
        return (ovf << 32) & cv

    @property
    def sys_time_s(self):
        """
        Get current sync device system time in seconds.
        
        Returns:
            float: System time in seconds
        """
        return float(self.get_property(props.ro_SYS_TIME_s))

    @property
    def prescaler(self):
        """
        Get the sync device timer prescaler value. The Arduino Due runs at 84 MHz,
        and the system timer is clocked at 84 MHz / prescaler. The prescaler defines
        the system time resolution (duration of one tick, ranging from 24 ns to 1.524 µs),
        as well as the maximum allowable timestamp value :math:`t_\\mathrm{max}`
        (:math:`2^{32}` ticks).
        
        :math:`t_\\mathrm{max}` is defined as :math:`2^{32} \\cdot \\mathrm{prescaler} / 84` µs,
        and ranges from 1min 42s to 1h 49min.

        Returns:
            int: Timer prescaler (2, 8, 32, or 128)

        Note:
            The prescaler is hardcoded in the firmware, and cannot be changed at runtime.

            See globals.h for the prescaler values and their corresponding
            system time resolution and maximum timestamp value.
        """
        return int(self.get_property(props.ro_SYS_TIMER_PRESCALER))

    @property
    def pulse_duration_us(self):
        """
        Get the default pulse duration in microseconds. The default pulse duration
        is the duration of a positive or negative pulse generated by the pos_pulse()
        and neg_pulse() methods, and can be changed at runtime.
        
        Returns:
            int: Default pulse duration in microseconds
        """
        return int(self.get_property(props.rw_DFLT_PULSE_DURATION_us))

    @pulse_duration_us.setter
    def pulse_duration_us(self, value):
        """
        Set the default pulse duration in microseconds. This will affect only subsequent
        calls to pos_pulse() and neg_pulse(), and not the pulse duration of any previously
        scheduled events.

        Args:
            value (int): Default pulse duration in microseconds
        """
        self.set_property(props.rw_DFLT_PULSE_DURATION_us, value)

    @property
    def watchdog_timeout_ms(self):
        """
        Get the watchdog timeout value in milliseconds. The watchdog is a safety feature
        that resets the sync device if it stops responding for a certain amount of time.
        This can happen i.e. if too many events are scheduled, and the sync device is not
        managing to process them in a timely manner.
        
        Returns:
            int: Watchdog timeout in milliseconds, 100 ms by default
        """
        return int(self.get_property(props.ro_WATCHDOG_TIMEOUT_ms))

    @property
    def N_events(self):
        """
        Get the number of scheduled events in the event queue.
        
        Returns:
            int: Number of events currently in the queue
        """
        return int(self.get_property(props.ro_N_EVENTS))

    @property
    def interlock_enabled(self):
        """
        Check if the laser interlock is enabled. The interlock is a safety feature
        that prevents the laser from being turned on if the interlock circuit is broken.
        By default, the interlock is active.
        
        Returns:
            bool: True if interlock is active, False otherwise
        """
        return self.get_property(props.rw_INTLCK_ENABLED) != '0'
    
    @interlock_enabled.setter
    def interlock_enabled(self, value):
        """
        Enable or disable the laser interlock. The interlock is a safety feature
        that prevents the laser from being turned on if the interlock circuit is broken.
        
        Args:
            value (bool): True to enable interlock, False to disable
        """
        self.set_property(props.rw_INTLCK_ENABLED, value)

    def get_function_addr(self):
        """
        Get the function address mapping from the device.
        
        Returns:
            dict: Mapping of function names to their addresses
        
        Note:
            This is used internally to map function addresses to readable names.
        """
        response = self.write("FUN")
        return {k: v for k, v in [l.split() for l in
            self.com.readall().decode().splitlines()]}

    def get_events(self, unit="ms"):
        """
        Get all scheduled events from the device queue.
        
        Args:
            unit (str): Time unit for timestamps ("cts", "us", or "ms")
        
        Returns:
            list: List of Event objects representing scheduled events
        
        Example:
            >>> events = sd.get_events("us")
            >>> for event in events:
            ...     print(f"{event.func} at {event.ts} {event.unit}")
        """
        presc = self.prescaler

        self.write("QUE")
        r = self.com.readall()
        events = []
        for offset in range(0, len(r), 28):  # Event is 28 bytes
            e = Event(r[offset : offset + 28])
            e.map_func(self.func_map)
            e.ts -= us2cts(UNIFORM_TIME_DELAY, presc)
            if unit in ["us", "ms"]:
                e.unit = unit
                e.ts = round(cts2us(e.ts, presc)*(0.001 if unit == "ms" else 1))
                e.intvl = round(cts2us(e.intvl, presc)*(0.001 if unit == "ms" else 1))
            events.append(e)
        return events

    def show_events(self, figsize=(12, 4), title=None):
        """
        Retrieve and visualize scheduled events from the device (always in microseconds).
        
        Args:
            figsize (tuple): Figure size (width, height)
            title (str, optional): Custom title for the plot
        
        Returns:
            matplotlib.figure.Figure: The generated plot figure
        
        Example:
            >>> fig = sd.show_events()
            >>> plt.show()
        """
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from collections import defaultdict
        
        # Get events from device (always in microseconds)
        events = self.get_events("us")
        
        if not events:
            print("No events scheduled on device")
            return None
        
        # Create figure and setup
        fig, ax = plt.subplots(figsize=figsize)
        
        # Configuration
        STATE_EVENTS = ['SET_PIN', 'TGL_PIN', 'EN__PIN', 'DIS_PIN', 'OPE_SHU', 'CLS_SHU', 'BST__ON', 'BST_OFF']
        ACTIVE_COLOR = 'grey'
        INACTIVE_COLOR = 'white'
        BOX_HEIGHT = 0.6
        BOX_Y_OFFSET = BOX_HEIGHT / 2
        DEFAULT_DURATION = 50
        INFINITE_EXTENSION = 1e9  # 1 billion seconds
        
        def get_group_name(event):
            """Get the group name for an event based on its function type."""
            if event.func in ['SET_PIN', 'TGL_PIN']:
                pin_name = event.arg1 if isinstance(event.arg1, str) else rev_pin_map[event.arg1]
                return f"{event.func}({pin_name})"
            elif event.func in ['EN__PIN', 'DIS_PIN']:
                pin_name = event.arg1 if isinstance(event.arg1, str) else rev_pin_map[event.arg1]
                return f"Enabled({pin_name})"
            elif event.func in ['OPE_SHU', 'CLS_SHU']:
                return "Shutter"
            elif event.func in ['BST__ON', 'BST_OFF']:
                return "Burst"
            else:
                return event.func
        
        def is_active_state(event):
            """Determine if an event represents an active state."""
            active_states = {
                'SET_PIN': lambda e: e.arg2 == 1,  # HIGH is active
                'TGL_PIN': lambda e: True,  # Toggle is always active
                'EN__PIN': lambda e: True,  # Enable is active
                'DIS_PIN': lambda e: False,  # Disable is inactive
                'OPE_SHU': lambda e: True,  # Open is active
                'CLS_SHU': lambda e: False,  # Close is inactive
                'BST__ON': lambda e: True,  # Burst on is active
                'BST_OFF': lambda e: False,  # Burst off is inactive
            }
            return active_states.get(event.func, lambda e: True)(event)
        
        def create_rectangle(x, y, width, color, hatch=None):
            """Create a rectangle patch with consistent styling."""
            return patches.Rectangle(
                (x, y - BOX_Y_OFFSET), width, BOX_HEIGHT,
                linewidth=1, edgecolor='black', facecolor=color, alpha=0.7,
                hatch=hatch
            )
        
        def plot_shutter_event(event, start_time, end_time, y_pos, color):
            """Plot a shutter event with transient state visualization."""
            try:
                shutter_delay = self.shutter_delay_us
            except:
                # Fallback if shutter_delay_us is not available
                shutter_delay = 1000  # Default 1ms shutter delay
            
            duration = end_time - start_time
            
            if event.func == 'OPE_SHU':
                # Opening: first shutter_delay is transient, then full open
                if duration <= shutter_delay:
                    # Entire duration is transient
                    rect = create_rectangle(start_time, y_pos, duration, color, hatch='///')
                    ax.add_patch(rect)
                else:
                    # Transient period (hatched)
                    rect_transient = create_rectangle(start_time, y_pos, shutter_delay, color, hatch='///')
                    ax.add_patch(rect_transient)
                    
                    # Full open period (solid)
                    rect = create_rectangle(start_time + shutter_delay, y_pos, duration - shutter_delay, color)
                    ax.add_patch(rect)
            else:  # CLS_SHU
                # Closing: first shutter_delay is transient, then fully closed
                if duration <= shutter_delay:
                    # Entire duration is transient
                    rect = create_rectangle(start_time, y_pos, duration, color, hatch='///')
                    ax.add_patch(rect)
                else:
                    # Transient period (hatched)
                    rect_transient = create_rectangle(start_time, y_pos, shutter_delay, color, hatch='///')
                    ax.add_patch(rect_transient)
                    
                    # Full closed period (solid)
                    rect = create_rectangle(start_time + shutter_delay, y_pos, duration - shutter_delay, color)
                    ax.add_patch(rect)
        
        def plot_state_events(group_events, y_pos, group_name):
            """Plot state-based events with proper state transitions."""
            # Expand and sort all repeating events
            expanded_events = []
            for event in group_events:
                expanded_events.extend(event.expand_repeating_events())
            
            if not expanded_events:
                return [], []
            
            sorted_events = sorted(expanded_events, key=lambda e: e.ts)
            all_ts = []
            all_ends = []
            
            # Track toggle state for TGL_PIN events
            toggle_state = False  # Start with unknown state
            current_hatch = '///'  # Start with forward slash pattern
            
            for i, event in enumerate(sorted_events):
                # Determine end time
                if i + 1 < len(sorted_events):
                    end_time = sorted_events[i + 1].ts
                else:
                    end_time = event.ts + INFINITE_EXTENSION
                
                # Handle TGL_PIN events specially
                if event.func == 'TGL_PIN':
                    # Toggle events use hatched pattern with alternating direction
                    rect = create_rectangle(event.ts, y_pos, end_time - event.ts, ACTIVE_COLOR, hatch=current_hatch)
                    ax.add_patch(rect)
                    # Flip hatch direction for next toggle
                    current_hatch = '\\\\\\' if current_hatch == '///' else '///'
                else:
                    # Determine color for non-toggle events
                    color = ACTIVE_COLOR if is_active_state(event) else INACTIVE_COLOR
                    
                    # Plot based on event type
                    if group_name == "Shutter" and event.func in ['OPE_SHU', 'CLS_SHU']:
                        plot_shutter_event(event, event.ts, end_time, y_pos, color)
                    else:
                        # Regular state event
                        rect = create_rectangle(event.ts, y_pos, end_time - event.ts, color)
                        ax.add_patch(rect)
                
                all_ts.append(event.ts)
                all_ends.append(end_time)
            
            return all_ts, all_ends
        
        def plot_non_state_events(group_events, y_pos):
            """Plot non-state events as simple rectangles."""
            all_ts = []
            all_ends = []
            
            for event in group_events:
                expanded_events = event.expand_repeating_events()
                
                for expanded_event in expanded_events:
                    rect = create_rectangle(expanded_event.ts, y_pos, DEFAULT_DURATION, ACTIVE_COLOR)
                    ax.add_patch(rect)
                    all_ts.append(expanded_event.ts)
                    all_ends.append(expanded_event.ts + DEFAULT_DURATION)
            
            return all_ts, all_ends
        
        # Group events
        event_groups = defaultdict(list)
        for event in events:
            group_name = get_group_name(event)
            event_groups[group_name].append(event)
        
        # Sort event groups by type and pin name
        def get_sort_key(group_name):
            """Get sorting key for group names."""
            # Extract event type and pin name for sorting
            if '(' in group_name and ')' in group_name:
                # Format: "EVENT_TYPE(PIN_NAME)" or "Enabled(PIN_NAME)"
                event_type = group_name.split('(')[0]
                pin_name = group_name.split('(')[1].rstrip(')')
                
                # Define event type priority order
                type_priority = {
                    'SET_PIN': 1,
                    'TGL_PIN': 2,
                    'Enabled': 3,
                    'Shutter': 4,
                    'Burst': 5
                }
                
                # Get priority for this event type (default to 999 for unknown types)
                priority = type_priority.get(event_type, 999)
                
                # Create a sortable key for pin names that handles numeric parts correctly
                def pin_sort_key(pin):
                    # Extract letter prefix and numeric suffix
                    import re
                    match = re.match(r'([A-Za-z]+)(\d*)', pin)
                    if match:
                        prefix, number = match.groups()
                        # Convert number to int for proper numeric sorting, default to 0 if no number
                        num = int(number) if number else 0
                        return (prefix, num)
                    else:
                        # Fallback for pins without numeric part
                        return (pin, 0)
                
                return (priority, pin_sort_key(pin_name))
            else:
                # For groups without pin names (like "Shutter", "Burst")
                type_priority = {
                    'Shutter': 4,
                    'Burst': 5
                }
                priority = type_priority.get(group_name, 999)
                return (priority, group_name)
        
        # Sort event groups
        sorted_groups = sorted(event_groups.items(), key=lambda x: get_sort_key(x[0]))
        
        # Plot events
        y_positions = {}
        y_pos = 0
        all_timestamps = []
        all_end_times = []
        
        for group_name, group_events in sorted_groups:
            if group_name not in y_positions:
                y_positions[group_name] = y_pos
                y_pos += 1
            
            y = y_positions[group_name]
            
            # Plot based on event type
            if group_events and group_events[0].func in STATE_EVENTS:
                ts, ends = plot_state_events(group_events, y, group_name)
            else:
                ts, ends = plot_non_state_events(group_events, y)
            
            all_timestamps.extend(ts)
            all_end_times.extend(ends)
        
        # Setup axes
        ax.set_ylim(-0.5, len(y_positions) - 0.5)
        ax.set_yticks(list(y_positions.values()))
        ax.set_yticklabels(list(y_positions.keys()))
        ax.set_xlabel('Time (us)')
        
        # Set title
        if title is None:
            title = f'Scheduled Events ({len(events)} total)'
        ax.set_title(title)
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='x')
        
        # Set x-axis limits
        if all_timestamps:
            min_ts = min(all_timestamps)
            max_ts = max(all_timestamps)
            time_range = max_ts - min_ts if max_ts > min_ts else 1
            pad_left = int(time_range * 0.02)
            pad_right = int(time_range * 0.2)
            ax.set_xlim(min_ts - pad_left, max_ts + pad_right)
        else:
            ax.set_xlim(0, 1)
        
        plt.tight_layout()
        return fig

    ## pTIRF extension
    def open_shutters(self, mask=0):
        """
        Open all laser shutters. Use the mask argument to specify which shutters to open.
        Omitting the mask argument will open all shutters.
        
        Args:
            mask (int): Bitmask specifying which shutters to open:

                * 0: Opens all shutters (note: This differs from the behavior of the mask in the `selected_lasers` property.)
                * 1: Cy2 only
                * 2: Cy3 only
                * 4: Cy5 only
                * 8: Cy7 only
                * Combinations: 1|2|4 = Cy2, Cy3, and Cy5
        
        Example:
            >>> sd.open_shutters()  # Open all shutters
            >>> sd.open_shutters(1 | 4)  # Open Cy2 and Cy5 only
        """
        self.set_property(props.wo_OPEN_SHUTTERS, mask)

    def close_shutters(self, mask=0):
        """
        Close all laser shutters. Use the mask argument to specify which shutters to close.
        Omitting the mask argument will close all shutters.
        
        Args:
            mask (int): Bitmask specifying which shutters to close:

                * 0: Closes all shutters (note: This differs from the behavior of the mask in the `selected_lasers` property.)
                * 1: Cy2 only
                * 2: Cy3 only
                * 4: Cy5 only
                * 8: Cy7 only
                * Combinations: 1|2|4 = Cy2, Cy3, and Cy5
        
        Example:
            >>> sd.close_shutters()   # Close all shutters
            >>> sd.close_shutters(2)  # Close Cy3 only
        """
        self.set_property(props.wo_CLOSE_SHUTTERS, mask)

    @property
    def selected_lasers(self):
        """
        Get the currently enabled laser channels. 
        
        Returns:
            int: Bitmask of enabled laser channels
        
        Example:
            >>> mask = sd.selected_lasers
            >>> print(f"Enabled lasers: {bin(mask)}")
        """
        return int(self.get_property(props.rw_SELECTED_LASERS))

    @selected_lasers.setter
    def selected_lasers(self, mask):
        """
        Set which laser channels are enabled.
        
        Args:
            mask (int): Bitmask of laser channels to enable:
                - 0: No lasers
                - 1: Cy2 only
                - 2: Cy3 only
                - 4: Cy5 only
                - 8: Cy7 only
                - Combinations: 1|2|4 = Cy2, Cy3, and Cy5
        
        Example:
            >>> sd.selected_lasers = 0b0110  # Enable Cy3 and Cy5
        """
        self.set_property(props.rw_SELECTED_LASERS, mask)
    
    @property
    def cam_readout_us(self):
        """
        Get the pre-programmed camera readout time.
        
        Returns:
            int: Pre-set camera readout time in microseconds
        """
        return int(self.get_property(props.rw_CAM_READOUT_us))

    @cam_readout_us.setter
    def cam_readout_us(self, value):
        """
        Set the camera readout time. Knowledge of correct camera readout time is required to properly
        schedule events using pTIRF extension functions such as start_continuous_acq(), start_stroboscopic_acq(),
        and start_ALEX_acq().
        
        Args:
            value (int): Camera readout time in microseconds

        Note:
            See manual for the specific camera model on how to determine the readout time.
        """
        self.set_property(props.rw_CAM_READOUT_us, value)

    @property
    def shutter_delay_us(self):
        """
        Get the pre-programmed laser shutter delay time.
        
        Returns:
            int: Shutter delay time in microseconds
        """
        return int(self.get_property(props.rw_SHUTTER_DELAY_us))

    @shutter_delay_us.setter
    def shutter_delay_us(self, value):
        """
        Set the laser shutter delay time, defined as the interval between issuing the
        shutter open command and the laser output reaching stable, steady-state power.
        This compensates for the finite response time of the shutter,
        ensuring accurate synchronization of illumination with camera exposure.
        
        Args:
            value (int): Shutter delay time in microseconds
        """
        self.set_property(props.rw_SHUTTER_DELAY_us, value)

    def start_continuous_acq(self, exp_time, N_frames, ts=0):
        """
        Start continuous acquisition mode.
        
        In continuous mode, laser shutters remain open during the entire acquisition
        and the camera is triggered at precise intervals. The first frame is
        automatically discarded as it contains pre-acquisition noise.
        
        Args:
            exp_time (int): Exposure time in microseconds
            N_frames (int): Number of frames to acquire
            ts (int): Start time offset in microseconds
        
        Example:
            >>> sd.start_continuous_acq(200000, 15, ts=500000)  # Acquire 15 frames with 200ms exposure, start at t=500ms
        """
        self.write("CON", arg1=exp_time, ts=ts, N=N_frames)

    def start_stroboscopic_acq(self, exp_time, N_frames, ts=0, frame_period=0):
        """
        Start stroboscopic or timelapse acquisition.
        
        In stroboscopic mode, the laser shutter is briefly opened during each camera
        exposure, followed by a readout period. The interval between frames is set by
        the optional frame_period parameter, which can be used to add a delay between
        laser pulses for timelapse acquisition.
        
        Args:
            exp_time (int): Exposure time in microseconds
            N_frames (int): Number of frames to acquire
            ts (int): Start time offset in microseconds
            frame_period (int): Time between frames for timelapse (microseconds)
        
        Example:
            >>> # Acquire 10 frames every 500ms with 100ms long laser exposure (timelapse mode)
            >>> sd.start_stroboscopic_acq(100000, 10, frame_period=500000)
        """
        self.write("STR", arg1=exp_time, ts=ts, N=N_frames, interval=frame_period)

    def start_ALEX_acq(self, exp_time, N_bursts, ts=0, burst_period=0):
        """
        Start ALEX (Alternating Laser Excitation) acquisition.
        
        In ALEX mode, frames are acquired in bursts, with each frame in a burst
        illuminated by a different laser channel. This enables multi-spectral imaging,
        and is useful for acquiring images of multiple fluorophores with different emission
        wavelengths.
        
        Args:
            exp_time (int): Exposure time in microseconds
            N_bursts (int): Number of bursts to acquire
            ts (int): Start time offset in microseconds
            burst_period (int): Time between bursts for timelapse (microseconds)
        
        Example:
            >>> sd.start_ALEX_acq(50000, 9, burst_period=400000)
        """
        self.write("ALX", arg1=exp_time, ts=ts, N=N_bursts, interval=burst_period)

    def N_frames_left(self):
        """
        Get the number of camera frames remaining in the current acquisition.
        
        Returns:
            int: Number of camera frames left to acquire, or 0 if no acquisition is running

        Note:
            In the ALEX mode, the number of frames left to acquire is the number of remaining
            bursts times the number of laser channels.
        
        Example:
            >>> frames_left = sd.N_frames_left()
            >>> print(f"Remaining frames: {frames_left}")
        """
        events = self.get_events()
        if events:
            for event in events:
                if rev_pin_map[event.arg1] == "A12":
                    return event.N
        return 0
