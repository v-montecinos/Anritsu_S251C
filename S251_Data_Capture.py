import argparse
import sys
import serial

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy.ndimage import gaussian_filter1d

_DEFAULT_PORT = "/dev/tty.usbserial-1420"
_DEFAULT_BAUD = 9600

# Map byte at offset 54 to number of sweep points (Anritsu protocol)
_DATA_POINTS_MAP = {0: 130, 1: 259}


def connect(port, baudrate=_DEFAULT_BAUD):
    try:
        print(f"\nTrying to open {port}")
        ser = serial.Serial(port, baudrate=baudrate)
        ser.write(b"\x45")
        return ser
    except serial.SerialException as e:
        print(f"Serial port open failed: {e}")
        sys.exit(1)


def read_data(ser):
    reply = ser.read(13)
    reply = reply.decode("utf-8", "ignore")
    model = reply[2:7]
    version = reply[9:13]

    print(f"Successful connected to {ser.name}")
    print(f"Anritsu SiteMaster {model}  Version {version} ")
    ser.write(b"\x11\x00")
    print("Retrieving the current trace")
    trace_data = ser.read(4364)
    ser.write(b"\xFF")
    ser.close()
    return trace_data


def calc_data(trace_data):
    td = trace_data
    measure_mode = hex(td[15])

    dp_byte = td[54]
    data_points = _DATA_POINTS_MAP.get(dp_byte, 517)

    start_freq = int.from_bytes(td[56:60], "big")
    stop_freq = int.from_bytes(td[60:64], "big")
    frequency = np.round(
        np.linspace(start_freq, stop_freq, data_points, dtype=np.float64) / 1e6,
        3,
    )

    # Each point: 4 payload bytes + 4 padding; payload is big-endian uint32 (gamma * scale in device units)
    raw = np.frombuffer(td, dtype=np.uint8, offset=228, count=data_points * 8)
    gamma_bytes = raw.reshape(data_points, 8)[:, :4]
    gamma = (
        gamma_bytes[:, 0].astype(np.uint32) << 24
        | gamma_bytes[:, 1].astype(np.uint32) << 16
        | gamma_bytes[:, 2].astype(np.uint32) << 8
        | gamma_bytes[:, 3].astype(np.uint32)
    )
    for i in range(len(gamma)):     #To avoid zero log
        if gamma[i] == 0:
            gamma[i] = 1
        else:
            pass
    return measure_mode, start_freq, stop_freq, frequency, gamma


_TRACE_CSV_COLUMNS = {
    "0x0": "Return_Loss_dB",
    "0x1": "SWR",
    "0x2": "Cable_Loss_dB",
    "0x21": "Insertion_Loss_dB",
    "0x22": "Insertion_Gain_dB",
}


def _save_csv(path, frequency_mhz, y, measure_mode):
    col_y = _TRACE_CSV_COLUMNS[measure_mode]
    data = np.column_stack([frequency_mhz, y])
    header = f"Frequency_MHz,{col_y}"
    np.savetxt(path, data, delimiter=",", header=header, comments="", fmt="%.6g")
    print(f"CSV saved: {path}")


def plot_data(
    measure_mode,
    start_freq,
    stop_freq,
    frequency,
    gamma,
    smooth,
    csv_path=None,
    png_path=None,
    show=True,
):
    specs = {
        "0x0": (
            lambda g: np.round(20 * np.log10(g / 1000), 3),
            "RETURN LOSS",
            "Return Loss [dB]",
            3,
        ),
        "0x1": (
            lambda g: np.round((1 + g / 1000) / (1 - g / 1000), 3),
            "SWR",
            "SWR",
            3,
        ),
        "0x2": (
            lambda g: np.round(20 * np.log10(g / 1000) / 2, 3),
            "CABLE LOSS",
            "Cable Loss [dB]",
            5,
        ),
        "0x21": (
            lambda g: np.round(20 * np.log10(g / 10000000), 3),
            "INSERTION LOSS",
            "Insertion Loss [dB]",
            3,
        ),
        "0x22": (
            lambda g: np.round(20 * np.log10(g / 10000000), 3),
            "INSERTION GAIN",
            "Insertion Gain [dB]",
            3,
        ),
    }

    if measure_mode not in specs:
        print("Measure Mode not supported")
        return

    fn, title, ylabel, poly = specs[measure_mode]
    y = fn(gamma)
    if smooth:
        y = gaussian_filter1d(y, sigma=2)

    if csv_path is not None:
        _save_csv(csv_path, frequency, y, measure_mode)

    need_figure = show or png_path is not None
    if not need_figure:
        return

    fig, ax = plt.subplots()
    ax.plot(frequency, y)
    ax.grid()
    ax.set_xlim(start_freq / 1e6, stop_freq / 1e6)
    ax.set_title(title)
    ax.set_xlabel("Frequency [MHz]")
    ax.set_ylabel(ylabel)
    fig.tight_layout()

    if png_path is not None:
        fig.savefig(png_path, dpi=150, bbox_inches="tight")
        print(f"PNG saved: {png_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Capture the current trace from an Anritsu SiteMaster (S251C) over serial port."
    )
    p.add_argument(
        "-p",
        "--port",
        default=_DEFAULT_PORT,
        help=f"Serial device path (default: {_DEFAULT_PORT!r})",
    )
    p.add_argument(
        "-b",
        "--baudrate",
        type=int,
        default=_DEFAULT_BAUD,
        help=f"Serial baud rate (default: {_DEFAULT_BAUD})",
    )
    p.add_argument(
        "--smooth",
        action="store_true",
        help="Enable smoothing for the trace and CSV export",
    )
    p.add_argument(
        "--csv",
        metavar="FILE",
        help="Write frequency (MHz) and trace values to a CSV file",
    )
    p.add_argument(
        "--png",
        metavar="FILE",
        help="Save the plot as a PNG image",
    )
    p.add_argument(
        "-n",
        "--no-show",
        action="store_true",
        help="Do not open a matplotlib window (useful with --csv and/or --png only)",
    )
    args = p.parse_args(argv)
    if args.no_show and not args.csv and not args.png:
        p.error("With --no-show, provide at least one of --csv or --png.")
    return args


def main(argv=None):
    args = parse_args(argv)
    smooth_plot = args.smooth
    ser = connect(args.port, args.baudrate)
    trace_data = read_data(ser)
    measure_mode, start_freq, stop_freq, frequency, gamma = calc_data(trace_data)
    plot_data(
        measure_mode,
        start_freq,
        stop_freq,
        frequency,
        gamma,
        smooth_plot,
        csv_path=args.csv,
        png_path=args.png,
        show=not args.no_show,
    )


if __name__ == "__main__":
    main()
