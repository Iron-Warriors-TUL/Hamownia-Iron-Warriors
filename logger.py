"""logger.py
This module provides functionality to log RPM, Torque, and Power data from a GPIO encoder.
"""

import math
from queue import Queue
from threading import Thread
from typing import List, Optional, Tuple
import csv
import settings


class Logger:
    """A class to handle logging of RPM, Torque, and Power data."""

    data_queue: Queue[Tuple[int, int, int]] = Queue()
    recording_active: bool = False
    rpm_log: List[float] = []
    torque_log: List[float] = []
    power_log: List[float] = []
    timestamp_log: List[float] = []

    def __init__(self) -> None:
        self.log_file = settings.LOG_FILE
        self.prev_omega: Optional[float] = None
        self.prev_time_s: Optional[float] = None
        self.thread = Thread(target=self.queue_writer, daemon=True)
        self.thread.start()

    def enque_data(self, pulses: int, delta_ns: int, now_ns: int) -> None:
        """Enqueue pulse count and timing for processing."""
        if self.recording_active:
            self.data_queue.put((pulses, delta_ns, now_ns))

    def compute_data(
        self, pulses: int, delta_ns: int, now_ns: int
    ) -> Tuple[float, float, float, float]:
        """Compute RPM, Torque, and Power from pulse count in a window."""
        window_s = delta_ns / 1e9
        freq_hz = pulses / window_s
        rpm: float = freq_hz * 60
        omega: float = 2 * math.pi * freq_hz
        now_s: float = now_ns / 1e9

        if self.prev_omega is not None and self.prev_time_s is not None:
            delta_omega: float = omega - self.prev_omega
            delta_t = now_s - self.prev_time_s
            torque: float = (
                settings.MOMENT_OF_INERTIA * delta_omega / delta_t if delta_t > 0 else 0
            )
        else:
            torque = 0

        power: float = torque * omega

        return rpm, omega, torque, power

    def queue_writer(self) -> None:
        """Write the logged data to a file."""

        with open(self.log_file, "w", newline="", encoding="utf-8") as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(
                ["Pulses", "RPM", "Δt(ns)", "ω(rad/s)", "Torque(Nm)", "Power(W)"]
            )

            while True:
                pulses, delta_ns, now_ns = self.data_queue.get()
                if not self.recording_active:
                    continue

                rpm, omega, torque, power = self.compute_data(pulses, delta_ns, now_ns)
                csv_writer.writerow(
                    [
                        pulses,
                        f"{rpm:.2f}",
                        f"{delta_ns:.2f}",
                        f"{omega:.2f}",
                        f"{torque:.3f}",
                        f"{power:.2f}",
                    ]
                )
                file.flush()
                self.rpm_log.append(rpm)
                self.torque_log.append(torque)
                self.power_log.append(power)
                self.timestamp_log.append(now_ns / 1e9)
                self.prev_omega = omega
                self.prev_time_s = now_ns / 1e9

    def clean_data(self) -> None:
        """Clear all logged data."""
        self.rpm_log.clear()
        self.torque_log.clear()
        self.power_log.clear()
        self.timestamp_log.clear()
