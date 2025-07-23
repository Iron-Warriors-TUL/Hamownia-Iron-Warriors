import datetime
import queue
from typing import List, Tuple

import settings


class Logger:
    def __init__(self):
        self.log_filename: str = f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.queue_data: queue.Queue[Tuple[int, int, int]] = queue.Queue()
        self.recording_active: bool = True
        self.rpm_log: List[Tuple[int, float]] = []
        self.torque_data: List[float] = []
        self.power_data: List[float] = []
        self.timestamp_log: List[float] = []

    def enqueue_data(self, pulse_count, delta_ns, now_ns):
        self.queue_data.put((pulse_count, delta_ns, now_ns))

    def start_logging(self):
        with open(self.log_filename, "w") as f:
            f.write("Index\tRPM\tΔt(ns)\tω(rad/s)\tTorque(Nm)\tPower(W)\n")

            while self.recording_active:
                if not self.queue_data.empty():
                    pulse_idx, delta_ns, now_ns = self.queue_data.get()
                    rpm = 60 * 1e9 / delta_ns
                    omega = 2 * 3.1416 * rpm / 60
                    now_s = now_ns / 1e9

                    if self.rpm_log:
                        prev_omega = self.rpm_log[-1][1]
                        prev_time_s = self.timestamp_log[-1]
                        delta_omega = omega - prev_omega
                        delta_t = now_s - prev_time_s
                        torque = settings.MOMENT_OF_INERTIA * delta_omega / delta_t if delta_t > 0 else 0
                    else:
                        torque = 0
                        delta_t = 0

                    power = torque * omega

                    # Log the data
                    f.write(f"{pulse_idx}\t{rpm:.2f}\t{delta_ns}\t{omega:.2f}\t{torque:.2f}\t{power:.2f}\n")
                    
                    # Store data for later use
                    self.rpm_log.append((pulse_idx, omega))
                    self.torque_data.append(torque)
                    self.power_data.append(power)
                    self.timestamp_log.append(now_s)