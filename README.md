# Anritsu MS2711D — trace capture

**Languages:** [English](README.md) · [Español](README.es.md)

Python utilities to read the current spectrum trace from an **Anritsu MS2711D** Spectrum Master over **serial** (remote mode), parse the binary payload, and **plot** or **export CSV**.

Programming reference: [Anritsu programming manual (10580-00098)](https://dl.cdn-anritsu.com/en-us/test-measurement/files/Manuals/Programming-Manual/10580-00098.pdf).

## Repository contents

| File | Description |
|------|-------------|
| `MS2111D_capture_data.py` | Original single-file script (simple flow). |
| `MS2111D_capture_data_optimized.py` | Refactored version: class-based API, CLI, configurable serial, CSV/image export. |

## Requirements

- **Python** 3.9 or newer (the optimized script uses typing compatible with 3.9; avoid `str \| None` style hints on older interpreters).
- Packages:
  - `pyserial`
  - `numpy`
  - `matplotlib`

Install (example with a virtual environment):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install pyserial numpy matplotlib
```

## Hardware / OS

- Connect the analyzer via USB–serial (or RS-232 adapter). On macOS/Linux the device is often `/dev/tty.usbserial-*` or `/dev/ttyUSB0`. Use the correct path with `--port`.
- Default port in code: `/dev/tty.usbserial-1420` — **change it** to match your system.

## Usage (optimized script)

Show help:

```bash
python3 MS2111D_capture_data_optimized.py --help
```

Capture and show the plot (default):

```bash
python3 MS2111D_capture_data_optimized.py
```

Custom serial settings:

```bash
python3 MS2111D_capture_data_optimized.py --port /dev/tty.usbserial-1410 --baudrate 9600 --timeout 10.0
```

Save trace data as CSV (frequency Hz, amplitude dBm):

```bash
python3 MS2111D_capture_data_optimized.py --save trace.csv
```

Save the figure without opening a window:

```bash
python3 MS2111D_capture_data_optimized.py --save plot.png --no-plot
```

### CLI options

| Option | Description |
|--------|-------------|
| `--port` | Serial device path (default: `/dev/tty.usbserial-1420`). |
| `--baudrate` | Baud rate (default: `9600`). |
| `--timeout` | Read timeout in seconds (default: `10.0`). Increase if the trace buffer is incomplete. |
| `--save` | If the path ends in `.csv`, saves numeric trace; otherwise saves the plot using the given image extension. |
| `--no-plot` | Do not open an interactive plot window. |

## Troubleshooting

- **`ModuleNotFoundError: No module named 'serial'`** — Install **pyserial** (`pip install pyserial`).
- **Incomplete trace buffer** (fewer than 2035 bytes) — Raise `--timeout` or check cable, port, and baud rate.
- **Cannot open serial port** — Verify the device path, permissions, and that no other program holds the port.
- **Matplotlib cache warnings** — Set a writable config dir, e.g. `export MPLCONFIGDIR=/path/to/writable/dir`.

## License / attribution

See source file headers. Copyright 2026 — Vicente Montecinos Gaete.
