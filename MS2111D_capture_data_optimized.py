# Python script to capture and plot the current trace from an Anritsu MS2711D
# spectrum analyzer over serial (remote mode), parse the binary trace block,
# and optionally plot or export CSV. See --help for CLI options.
# REF: https://dl.cdn-anritsu.com/en-us/test-measurement/files/Manuals/Programming-Manual/10580-00098.pdf
# Copyright 2026 - Vicente Montecinos Gaete

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import serial

# Protocol / trace layout (per instrument programming manual).
DATA_POINTS = 401  # Number of sweep points per trace.
DEFAULT_PORT = "/dev/tty.usbserial-1420"
TRACE_BUFFER_SIZE = 2035  # Expected byte count for the trace read command.
DEFAULT_BAUDRATE = 9600
DEFAULT_TIMEOUT = 10.0  # Serial read timeout (s); increase if reads return short buffers.


def positive_int(value: str) -> int:
    """argparse type: strictly positive integer."""
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be > 0.")
    return parsed


def positive_float(value: str) -> float:
    """argparse type: strictly positive float (e.g. timeout)."""
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be > 0.")
    return parsed


@dataclass
class TraceData:
    """Parsed trace metadata plus aligned frequency and amplitude arrays."""

    start_freq: int  # Hz, sweep start
    stop_freq: int  # Hz, sweep stop
    span: int  # Hz (stop - start)
    frequency: np.ndarray  # Hz, length == DATA_POINTS
    amplitude: np.ndarray  # dBm
    center: int  # Hz
    date: str  # ASCII from buffer
    time: str
    rbw: int  # Hz, resolution bandwidth
    vbw: int  # Hz, video bandwidth
    att: float  # dB (raw from buffer / 1000)


class MS2711DAnalyzer:
    """Serial capture, binary parsing, and matplotlib/CSV output."""

    def __init__(
        self,
        port: str,
        data_points: int = DATA_POINTS,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.port = port
        self.data_points = data_points
        self.baudrate = baudrate
        self.timeout = timeout

    def capture_trace(self) -> bytes:
        """Open port, enter remote mode, read trace block, exit remote mode."""
        try:
            print(f"\nTrying to open {self.port}")
            with serial.Serial(
                self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            ) as ser:
                # 0x45: remote ON (PC control).
                ser.write(b"\x45")  # enter remote mode
                id_buffer = ser.read(13).decode("utf-8", "ignore")
                model = id_buffer[2:9]
                version = id_buffer[9:13]
                # 0x21 0x00: request trace (fixed-size binary payload).
                ser.write(b"\x21\x00")
                buffer = ser.read(TRACE_BUFFER_SIZE)
                # 0xFF: remote OFF (front panel control).
                ser.write(b"\xFF")  # leave remote mode
                if len(buffer) != TRACE_BUFFER_SIZE:
                    print(
                        f"Incomplete trace buffer: got {len(buffer)} bytes, "
                        f"expected {TRACE_BUFFER_SIZE}. "
                        "Increase --timeout or check serial link."
                    )
                    sys.exit(1)
                print(
                    f"Anritsu Spectrum Master {model} "
                    f"Version {version}, connected to {ser.name}"
                )
                return buffer
        except serial.SerialException as exc:
            print(f"Serial port open failed: {exc}")
            sys.exit(1)

    def parse_trace(self, buffer: bytes) -> TraceData:
        """Decode fixed byte offsets (big-endian) and build the frequency axis."""
        # Start/stop/center frequencies (uint32, Hz).
        start_freq = int.from_bytes(buffer[56:60], "big")
        stop_freq = int.from_bytes(buffer[60:64], "big")
        span = stop_freq - start_freq
        frequency = np.linspace(start_freq, stop_freq, self.data_points)

        # Amplitude sweep: 401 samples × 4 bytes, big-endian, starting at offset 431.
        amplitude_raw = np.frombuffer(
            buffer,
            dtype=">u4",
            count=self.data_points,
            offset=431,
        )
        # Manual scaling: raw / 1000 - 270 -> dBm.
        amplitude = np.round((amplitude_raw / 1000.0) - 270.0, 3)

        center = int.from_bytes(buffer[64:68], "big")
        date = buffer[20:30].decode("utf-8", "ignore")
        time = buffer[30:38].decode("utf-8", "ignore")
        rbw = int.from_bytes(buffer[260:264], "big")
        vbw = int.from_bytes(buffer[264:268], "big")
        att = int.from_bytes(buffer[271:275], "big") / 1000

        return TraceData(
            start_freq=start_freq,
            stop_freq=stop_freq,
            span=span,
            frequency=frequency,
            amplitude=amplitude,
            center=center,
            date=date,
            time=time,
            rbw=rbw,
            vbw=vbw,
            att=att,
        )

    @staticmethod
    def unit(value: float) -> str:
        """Format Hz for axis labels (GHz / MHz / kHz / Hz)."""
        if value >= 1e9:
            return f"{value / 1e9} GHz"
        if value >= 1e6:
            return f"{value / 1e6} MHz"
        if value >= 1e3:
            return f"{value / 1e3} KHz"
        return f"{value} Hz"

    @staticmethod
    def ticks(center: int, span: int) -> tuple[float, float]:
        """X-axis tick spacing and divisor for readable tick labels."""
        space = span / 10
        if center >= 1e9:
            divider = 1e9
        elif center >= 1e6:
            divider = 1e6
        elif center >= 1e3:
            divider = 1e3
        else:
            divider = 1
        return space, divider

    def plot_trace(self, trace: TraceData, show_plot: bool = True, save_path: Optional[str] = None) -> None:
        """Plot dBm vs frequency; optionally save figure and/or show interactive window."""
        space, divider = self.ticks(trace.center, trace.span)
        x_ticks = np.arange(trace.start_freq, trace.stop_freq + space, space)

        plt.figure(figsize=(10, 8))
        plt.plot(trace.frequency, trace.amplitude)
        plt.grid()
        plt.xlim(trace.start_freq, trace.stop_freq)
        plt.title(f"{trace.date} {trace.time}")
        plt.xlabel(
            f"Center {self.unit(trace.center)}\n\n"
            f"ATT {trace.att} dB    RBW {self.unit(trace.rbw)}    "
            f"VBW {self.unit(trace.vbw)}    Span {self.unit(trace.span)}\n"
        )
        plt.xticks(x_ticks, x_ticks / divider)
        plt.ylabel("Amplitude [dBm]")

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"Plot saved to: {save_path}")

        if show_plot:
            plt.show()
        else:
            plt.close()

    @staticmethod
    def save_trace_csv(trace: TraceData, csv_path: str) -> None:
        """Export two columns: frequency (Hz) and amplitude (dBm)."""
        data = np.column_stack((trace.frequency, trace.amplitude))
        header = "frequency_hz,amplitude_dbm"
        np.savetxt(csv_path, data, delimiter=",", header=header, comments="")
        print(f"Trace data saved to: {csv_path}")


def parse_args() -> argparse.Namespace:
    """CLI: port, baudrate, timeout, save path (.csv or image), optional no GUI."""
    parser = argparse.ArgumentParser(description="Capture trace from Anritsu MS2711D.")
    parser.add_argument("--port", default=DEFAULT_PORT, help="Serial port path.")
    parser.add_argument(
        "--baudrate",
        type=positive_int,
        default=DEFAULT_BAUDRATE,
        help="Serial baudrate (default: 9600).",
    )
    parser.add_argument(
        "--timeout",
        type=positive_float,
        default=DEFAULT_TIMEOUT,
        help=f"Serial read timeout in seconds (default: {DEFAULT_TIMEOUT}).",
    )
    parser.add_argument(
        "--save",
        help="Save output. Use .csv to save trace data or image extension to save plot.",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Do not show interactive plot window.",
    )
    return parser.parse_args()


def main() -> None:
    """Capture and parse; .csv writes numeric data; other --save saves the plot image."""
    args = parse_args()
    analyzer = MS2711DAnalyzer(
        port=args.port,
        baudrate=args.baudrate,
        timeout=args.timeout,
    )
    buffer = analyzer.capture_trace()
    trace = analyzer.parse_trace(buffer)

    save_path = args.save
    # .csv: export columns only; still plot unless --no-plot.
    if save_path and Path(save_path).suffix.lower() == ".csv":
        analyzer.save_trace_csv(trace, save_path)
        if not args.no_plot:
            analyzer.plot_trace(trace, show_plot=True)
        return

    # Interactive plot and/or image file from --save extension.
    analyzer.plot_trace(
        trace,
        show_plot=not args.no_plot,
        save_path=save_path,
    )


if __name__ == "__main__":
    main()
