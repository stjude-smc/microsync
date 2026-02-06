# `microsync` — Python driver for microscope synchronization device

**Python driver for `microsync` — a universal 32-bit Arduino Due-based triggering device**. Control lasers, cameras, and timing with microsecond precision.

- **Full documentation:** [stjude-smc.github.io/microsync](https://stjude-smc.github.io/microsync/)
- **Repository:** [github.com/stjude-smc/microsync](https://github.com/stjude-smc/microsync)

## Install

Requires Python 3.7+ and `pyserial` (installed automatically):

```bash
pip install microsync
```

## Quick start

Upload the microsync firmware to an Arduino Due, then:

```python
from microsync import SyncDevice

sd = SyncDevice("COM4")   # or "/dev/ttyUSB0" on Linux
sd.pos_pulse("D8", 1000, ts=1000)   # 1 ms pulse on D8 after 1 ms delay
sd.go()
```

## Features

- Microsecond-precision event scheduling (pulses, toggles, camera triggers)
- Laser shutter and interlock safety logic
- Acquisition modes: continuous, stroboscopic, ALEX
- Interactive event visualization (Bokeh)
- Context manager for jitter-free batch commands

