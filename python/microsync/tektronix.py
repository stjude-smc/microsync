import re
import time

try:
    import numpy as np
    import pandas as pd
except ImportError as exc:
    raise ImportError(
        "microsync.tektronix requires the 'jitter' extra. "
        "Install with: pip install \"microsync[jitter]\""
    ) from exc

class _Channel:
    def __init__(self, parent, idx):
        parent._chk_ch(idx)
        self._p = parent
        self._i = idx
        # Cache for this channel's waveform parameters
        self._preamble_cache = None

    @property
    def scale(self) -> float:  # V/div
        return self._p._qnum(f"CH{self._i}:SCALE?")

    @scale.setter
    def scale(self, val: float):
        self._p.io.write(f"CH{self._i}:SCALE {val}")
        self._invalidate_cache()  # Clear this channel's cache when scale changes

    @property
    def position(self) -> float:  # divisions
        return self._p._qnum(f"CH{self._i}:POSITION?")

    @position.setter
    def position(self, val: float):
        self._p.io.write(f"CH{self._i}:POSITION {val}")
        self._invalidate_cache()  # Clear this channel's cache when position changes

    def _invalidate_cache(self):
        """Invalidate this channel's waveform cache."""
        self._preamble_cache = None

    def _get_preamble(self):
        """Get cached waveform preamble for this channel."""
        if self._preamble_cache is None:
            # Set this channel as data source
            self._p.io.write(f"DATA:SOURCE CH{self._i}")
            # Fetch and cache the preamble
            self._preamble_cache = {
                'YMULT': self._p._qnum("WFMPRE:YMULT?"),
                'YZERO': self._p._qnum("WFMPRE:YZERO?"),
                'YOFF':  self._p._qnum("WFMPRE:YOFF?"),
            }
        return self._preamble_cache


class _Trigger:
    def __init__(self, parent):
        self._p = parent

    @property
    def source(self) -> str:
        # CH1..CH4, EXT, EXT5 (if present), LINE
        return self._p.io.query("TRIGGER:MAIN:EDGE:SOURCE?").strip()

    @source.setter
    def source(self, val: str):
        val = val.upper()
        allowed = {f"CH{i}" for i in range(1,5)} | {"EXT", "LINE"}
        if val not in allowed:
            raise ValueError(f"source must be one of {sorted(allowed)}")
        self._p.io.write(f"TRIGGER:MAIN:EDGE:SOURCE {val}")

    @property
    def level(self) -> float:
        return self._p.io.query("TRIGGER:MAIN:LEVEL?").strip()

    @level.setter
    def level(self, val):
        self._p.io.write(f"TRIGGER:MAIN:LEVEL {val}")
    
    @property
    def mode(self) -> str:
        # AUTO or NORMal
        return self._p.io.query("TRIGGER:MAIN:MODE?").strip()

    @mode.setter
    def mode(self, val: str):
        val = val.upper()
        if val in ("NORMAL", "NORM"):
            val = "NORMal"
        elif val == "AUTO":
            val = "AUTO"
        else:
            raise ValueError("mode must be 'AUTO' or 'NORMal'")
        self._p.io.write(f"TRIGGER:MAIN:MODE {val}")

    def force(self):
        """Force a trigger event (does not start acquisition if stopped)."""
        self._p.io.write("TRIGGER:FORCE")

class _Acquire:
    def __init__(self, parent):
        self._p = parent
        
    # ACQUIRE:STATE?  -> '0' or '1'
    @property
    def state(self) -> bool:
        return bool(int(self._p.io.query("ACQUIRE:STATE?").strip()))

    @state.setter
    def state(self, running: bool):
        self._p.io.write(f"ACQUIRE:STATE {'RUN' if running else 'STOP'}")

    def stop(self):
        self._p.io.write("ACQUIRE:STATE STOP")

    def run(self):
        self._p.io.write("ACQUIRE:STATE RUN")

    # ACQUIRE:STOPAFTER? / ACQUIRE:STOPAFTER SEQ|RUNSTOP
    @property
    def stopafter(self) -> str:
        return self._p.io.query("ACQUIRE:STOPAFTER?").strip().upper()

    @stopafter.setter
    def stopafter(self, mode: str):
        m = mode.strip().upper()
        if m in ("SEQ", "SEQUENCE"):
            m = "SEQUENCE"
        elif m in ("RUNSTOP", "RUN/STOP"):
            m = "RUNSTOP"
        else:
            raise ValueError("stopafter must be SEQUENCE or RUNSTOP")
        self._p.io.write(f"ACQUIRE:STOPAFTER {m}")

    def arm_single(self):
        """Equivalent to:
           ACQUIRE:STATE STOP
           ACQUIRE:STOPAFTER SEQ
           ACQUIRE:STATE RUN
        """
        self.stop()
        self.stopafter = "SEQUENCE"
        self.run()

    def wait_until_stopped(self, timeout_s: float = 5.0, poll_s: float = 0.05) -> bool:
        """
        Block until ACQUIRE:STATE? == 0 (stopped) or timeout.
        Returns True if stopped, False on timeout.
        """
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if not self.state:
                return True
            time.sleep(poll_s)
        return False
        
    @property
    def state(self) -> bool:
        # True=running, False=stopped
        return bool(int(self._p.io.query("ACQUIRE:STATE?").strip()))

    @state.setter
    def state(self, running: bool):
        self._p.io.write(f"ACQUIRE:STATE {'RUN' if running else 'STOP'}")

    def run(self):
        self.state = True

    def stop(self):
        self.state = False

    def single(self, wait: bool = True, timeout_s: float = 3.0):
        """
        Arm single-sequence acquisition and (optionally) wait until done.
        """
        self._p.io.write("ACQUIRE:STOPAFTER SEQUENCE")
        # Clear event status and set *OPC to signal completion
        self._p.io.write("*CLS")
        self._p.io.write("ACQUIRE:STATE RUN")
        if wait:
            old_to = self._p.io.timeout
            try:
                # pyvisa timeout is in ms
                self._p.io.timeout = int(max(timeout_s, 0.05) * 1000)
                # *OPC? blocks until acquisition complete
                self._p.io.query("*OPC?")
            finally:
                self._p.io.timeout = old_to
        # return to continuous stop-after (optional; comment out if you prefer SEQUENCE to persist)
        self._p.io.write("ACQUIRE:STOPAFTER RUNSTOP")


class TDS2004:
    def __init__(self, resource):
        """
        resource: an open pyvisa resource (e.g., from rc.open_resource(...))
        """

        # TODO: automatically find the resource if not provided

        # TODO: set oscilloscope to default settings

        self.io = resource
        # Tektronix usually wants \n line termination
        self.io.write_termination = '\n'
        self.io.read_termination  = '\n'
        self.ch = {i: _Channel(self, i) for i in range(1, 5)}
        self.trig = _Trigger(self)
        self.acq  = _Acquire(self)
        
        # Setup oscilloscope for fast binary data transfer
        self._setup_binary_transfer()
        
        # Cache for X-axis (horizontal) parameters
        self._x_axis_cache = None

    # --- helpers ---
    @staticmethod
    def _to_number(s: str) -> float:
        """
        Convert Tek 'engineering notation' strings to float.
        Accepts forms like '2.0E-3', '5m', '1.2 k', '10uV', '2.5 s', etc.
        """
        s = s.strip()
        # try plain float first (covers 1.23E-6, etc.)
        try:
            return float(s)
        except ValueError:
            pass

        # strip units/spaces, capture optional SI suffix
        m = re.fullmatch(r'\s*([+-]?[\d_]*\.?\d+(?:[eE][+-]?\d+)?)\s*([yzafpnumkKMGT]?)(?:[A-Za-z/]+)?\s*', s)
        if not m:
            raise ValueError(f"Cannot parse number: {s}")

        base, suffix = m.group(1), m.group(2)
        x = float(base)
        si = {
            'y': 1e-24, 'z': 1e-21, 'a': 1e-18, 'f': 1e-15, 'p': 1e-12,
            'n': 1e-9,  'u': 1e-6,  'm': 1e-3,  'k': 1e3,   'K': 1e3,
            'M': 1e6,   'G': 1e9,   'T': 1e12,  '': 1.0
        }
        return x * si.get(suffix, 1.0)

    def _qnum(self, cmd: str) -> float:
        return self._to_number(self.io.query(cmd))
    
    def _setup_binary_transfer(self):
        """Configure oscilloscope for fast binary data transfer."""
        # Set up binary data format - do this once during init
        self.io.write("DATA:ENCDG RIBINARY")
        self.io.write("WFMPre:BYT_Or LSB")
        # Use 8-bit width for faster transfer (TDS2000 has 8-bit ADC anyway)
        self.io.write("DATA:WIDTH 1")

    @staticmethod
    def _chk_ch(ch: int) -> int:
        if ch not in (1, 2, 3, 4):
            raise ValueError("Channel must be 1..4")
        return ch

    # --- vertical (per-channel) ---
    def get_vscale(self, ch: int) -> float:
        ch = self._chk_ch(ch)
        return self._qnum(f"CH{ch}:SCALE?")          # V/div

    def get_vpos(self, ch: int) -> float:
        ch = self._chk_ch(ch)
        return self._qnum(f"CH{ch}:POSITION?")       # divisions

    # --- horizontal (main) ---
    def get_hscale(self) -> float:
        return self._qnum("HORIZONTAL:MAIN:SCALE?")  # s/div

    def get_hpos(self) -> float:
        return self._qnum("HORIZONTAL:MAIN:POSITION?")  # divisions
    
    @property
    def hscale(self) -> float:  # s/div
        return self._qnum("HORIZONTAL:MAIN:SCALE?")
    
    @hscale.setter
    def hscale(self, val: float):
        self.io.write(f"HORIZONTAL:MAIN:SCALE {val}")
        self._invalidate_x_axis_cache()  # Clear X-axis cache when horizontal scale changes
    
    @property
    def hpos(self) -> float:    # divisions
        return self._qnum("HORIZONTAL:MAIN:POSITION?")
    
    @hpos.setter
    def hpos(self, val: float):
        self.io.write(f"HORIZONTAL:MAIN:POSITION {val}")
        self._invalidate_x_axis_cache()  # Clear X-axis cache when horizontal position changes
        
    def _get_x_axis_preamble(self):
        """Get cached X-axis (horizontal) parameters."""
        if self._x_axis_cache is None:
            # Fetch and cache the X-axis parameters
            self._x_axis_cache = {
                'XINCR': self._qnum("WFMPRE:XINCR?"),
                'XZERO': self._qnum("WFMPRE:XZERO?"),
                'NR_PT': int(self.io.query("WFMPRE:NR_PT?")),
            }
        return self._x_axis_cache
    
    def _invalidate_x_axis_cache(self):
        """Invalidate the X-axis cache."""
        self._x_axis_cache = None
    
    def update_preamble(self):
        """Explicitly update all caches (4x channels + X-axis)."""
        # Clear all channel caches
        for ch in self.ch.values():
            ch._invalidate_cache()
        # Clear X-axis cache
        self._invalidate_x_axis_cache()
    
    def read_curve(self, ch: int):
        """
        Fetch waveform from CHx, scale to seconds/volts, return (t, y).
        Uses 8-bit data for faster transfer (TDS2000 has 8-bit ADC anyway).
        
        Note: start/stop parameters removed for speed. Use full waveform.
        """
        ch = self._chk_ch(ch)
        channel = self.ch[ch]
        
        # Get cached channel-specific preamble (Y-axis parameters)
        y_pre = channel._get_preamble()
        
        # Get cached X-axis parameters
        x_pre = self._get_x_axis_preamble()
        
        # Use 8-bit signed data for faster transfer
        self.io.write(f"DATA:SOURCE CH{ch}")
        raw = self.io.query_binary_values("CURVE?", datatype='b', container=np.array)
    
        # Scale to engineering units
        y = (raw - y_pre['YOFF']) * y_pre['YMULT'] + y_pre['YZERO']
        t0 = x_pre['XZERO']
        t = t0 + np.arange(raw.size) * x_pre['XINCR']
        return t, y
    
    def read_curves(self, channels: list):
        """
        Read multiple channels efficiently. Returns dict of {ch: (t, y)}.
        
        Args:
            channels: List of channel numbers (1-4)
            
        Returns:
            dict: {channel: (time_array, voltage_array)}
        """
        results = {}
        for ch in channels:
            ch = self._chk_ch(ch)
            results[ch] = self.read_curve(ch)
        return results
    
    def read_curves_df(self, channels: list):
        """
        Read multiple channels and return as pandas DataFrame.
        
        Args:
            channels: List of channel numbers (1-4)
            
        Returns:
            pandas.DataFrame: DataFrame with columns 'time', 'CH1', 'CH2', etc.
        """
        curves = self.read_curves(channels)
        
        # Use the time array from the first channel (all should be the same)
        first_ch = list(curves.keys())[0]
        time_data = curves[first_ch][0]
        
        # Create DataFrame with time column
        df = pd.DataFrame({'time': time_data})
        
        # Add voltage columns for each channel
        for ch in sorted(curves.keys()):
            df[f'CH{ch}'] = curves[ch][1]
        
        return df

