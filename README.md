# Anritsu SiteMaster S251C — trace capture

Small Python utility to enter remote mode on an **Anritsu SiteMaster** (tested with **S251C**), download the **current sweep trace** over RS-232/USB-serial, convert it by measurement mode, and plot or export **CSV** / **PNG**.

## Requirements

- Python 3.9+ (recommended)
- Packages:

```bash
pip install pyserial numpy matplotlib scipy
```

## Hardware / serial port

1. Connect the instrument via USB-serial (or RS-232 adapter).
2. Set `--port` to your OS device path. The built-in default is a typical macOS USB-serial name:

   `/dev/tty.usbserial-1420`

   On Linux use e.g. `/dev/ttyUSB0`; on Windows, `COM3` (or whatever Device Manager shows).

3. Default baud rate is **9600** (`-b` / `--baudrate`).

## Usage

```bash
python S251_Data_Capture.py --help
```

### Basic

```bash
python S251_Data_Capture.py
```

Opens a matplotlib window with the trace (no Savitzky–Golay smoothing unless you ask for it).

### Common options

| Option | Description |
|--------|-------------|
| `-p`, `--port` | Serial device path |
| `-b`, `--baudrate` | Baud rate (default: 9600) |
| `--smooth` | Enable Savitzky–Golay smoothing on trace and CSV |
| `--csv FILE` | Export frequency (MHz) + trace column to CSV |
| `--png FILE` | Save plot as PNG (150 dpi) |
| `-n`, `--no-show` | Do not open a GUI window (requires `--csv` and/or `--png`) |

### Examples

```bash
# Custom port
python S251_Data_Capture.py -p /dev/ttyUSB0

# Smoothing + save PNG only (no window)
python S251_Data_Capture.py --smooth --png trace.png -n

# CSV only (no plot window)
python S251_Data_Capture.py --csv sweep.csv -n

# CSV + PNG + on-screen plot
python S251_Data_Capture.py --csv sweep.csv --png sweep.png
```

### Headless systems (no display)

If saving PNG without a display fails, try:

```bash
export MPLBACKEND=Agg
python S251_Data_Capture.py --png out.png -n
```

## Supported measurement modes (frequency sweep)

The script maps the instrument’s mode byte to the same quantities as the on-device frequency-domain modes:

| Mode |
|----------|
| Return loss (dB) |
| SWR |
| Cable loss (dB) |
| Insertion loss (dB) |
| Insertion gain (dB) |

Other modes print `Measure Mode not supported` and skip plotting/export.

## CSV format

Two columns with header:

- `Frequency_MHz` — sweep frequency in MHz  
- Second column name depends on mode (e.g. `Return_Loss_dB`, `SWR`, `Cable_Loss_dB`, `Insertion_Loss_dB`, `Insertion_Gain_dB`)

Values match what is plotted (including `--smooth` when enabled).


## Protocol notes (short)

- Opens serial, sends remote command `0x45`, reads identity, requests trace with `0x11 0x00`, reads **4364** bytes, sends `0xFF` and closes the port.
- Sweep length is inferred from the trace header (130, 259, or 517 points).

If something fails, check cable, port name, baud rate, and that the instrument has a valid trace stored for the current setup.
