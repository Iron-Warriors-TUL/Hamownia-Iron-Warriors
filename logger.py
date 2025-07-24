"""logger.py
This module provides functionality to log RPM, Torque, and Power data from a GPIO encoder.
"""

from queue import Queue
from typing import List, Tuple, Optional
from datetime import datetime
import settings
from threading import Thread


class Logger:
    """A class to handle logging of RPM, Torque, and Power data."""

    data_queue: Queue[Tuple[int, int, int]] = Queue()
    recording_active: bool = False
    rpm_log: List[float] = []
    torque_log: List[float] = []
    power_log: List[float] = []
    timestamp_log: List[float] = []

    def __init__(self) -> None:
        self.log_file = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.prev_omega: Optional[float] = None
        self.prev_time_s: Optional[float] = None
        self.thread = Thread(target=self.queue_writer, daemon=True)
        self.thread.start()

    def enque_data(self, pulse_idx: int, delta_ns: int, now_ns: int) -> None:
        """Enqueue data for processing."""
        if self.recording_active:
            self.data_queue.put((pulse_idx, delta_ns, now_ns))

    def compute_data(
        self, delta_ns: int, now_ns: int
    ) -> Tuple[float, float, float, float]:
        """Compute RPM, Torque, and Power from the encoder data."""
        rpm: float = 60 * 1e9 / delta_ns
        omega: float = (2 * 3.14159 * rpm) / 60
        now_s: float = now_ns / 1e9

        if self.prev_omega is not None and self.prev_time_s is not None:
            delta_omega: float = omega - self.prev_omega
            delta_t = now_s - self.prev_time_s
            torque: float = (
                settings.MOMENT_OF_INERTIA * delta_omega / delta_t if delta_t > 0 else 0
            )
        else:
            torque: float = 0
            delta_t: float = 0

        power: float = torque * omega

        return rpm, omega, torque, power

    def queue_writer(self) -> None:
        """Write the logged data to a file."""
        with open(self.log_file, "w", encoding="utf-8") as file:
            file.write("Index\tRPM\tΔt(ns)\tω(rad/s)\tTorque(Nm)\tPower(W)\n")

            while True:
                pulse_idx, delta_ns, now_ns = self.data_queue.get()
                if not self.recording_active:
                    continue

                rpm, omega, torque, power = self.compute_data(delta_ns, now_ns)
                file.write(
                    f"{pulse_idx}\t{rpm:.2f}\t{delta_ns:.2f}\t{omega:.2f}\t{torque:.3f}\t{power:.2f}\n"
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
