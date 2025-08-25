"""gpio.py
This module provides functionality to handle GPIO encoder input for RPM measurement using frequency counting.
"""

import math
import time
import random
import threading
from typing import Optional

from logger import Logger
from mocks import MockGPIO
import settings

try:
    import RPi.GPIO as GPIO
except ImportError:
    from mocks import GPIO


class GPIOHandler:
    """A class to handle GPIO encoder input for RPM measurement."""

    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.pulse_count_window = 0
        self.window_ns = settings.WINDOW_SIZE_NS
        self.last_window_ns = time.time_ns()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(settings.ENCODER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            settings.ENCODER_PIN, GPIO.FALLING, callback=self._encoder_callback
        )

        # Start frequency window monitor
        self.window_thread = threading.Thread(target=self._window_monitor, daemon=True)
        self.window_thread.start()

        # Start simulation if using mock
        if isinstance(GPIO, MockGPIO):
            self.simulation_thread = threading.Thread(
                target=self.simulate_rpm_changes, daemon=True
            )
            self.simulation_thread.start()

    def _encoder_callback(self, _):
        """Just increment pulse counter."""
        self.pulse_count_window += 1

    def _window_monitor(self):
        """Every window, compute pulse count and enqueue data."""
        while True:
            now_ns = time.time_ns()
            if now_ns - self.last_window_ns >= self.window_ns:
                elapsed_ns = now_ns - self.last_window_ns
                pulses = self.pulse_count_window
                self.pulse_count_window = 0
                self.last_window_ns = now_ns

                if pulses > 0:
                    self.logger.enque_data(pulses, elapsed_ns, now_ns)

            time.sleep(self.window_ns / 1e9 / 10)  # check 10x per window

    def simulate_rpm_changes(self):
        """Simulate a very smooth dyno run profile with minimal noise."""
        start_time = time.time()
        total_duration = 60
        ramp_up_duration = 45
        max_rpm = 5000
        min_rpm = 100

        while True:
            elapsed = time.time() - start_time
            if elapsed >= total_duration:
                break

            if elapsed < ramp_up_duration:
                target_rpm = min_rpm + (elapsed / ramp_up_duration) * (
                    max_rpm - min_rpm
                )
            else:
                target_rpm = max_rpm

            # Small oscillations
            oscillation_amplitude = 0.002
            oscillation_frequency = 0.3
            oscillation = oscillation_amplitude * math.sin(
                elapsed * 2 * math.pi * oscillation_frequency
            )
            target_rpm += target_rpm * oscillation
            target_rpm = max(target_rpm, min_rpm)

            # Calculate timing
            target_delta_ns = (60 * 1e9) / target_rpm
            sleep_time = target_delta_ns / 1e9

            jitter = random.uniform(-0.0005, 0.0005)
            sleep_time = sleep_time * (1 + jitter)
            sleep_time = min(sleep_time, 0.1)

            if isinstance(GPIO, MockGPIO):
                GPIO.trigger(settings.ENCODER_PIN)

            time.sleep(sleep_time)
