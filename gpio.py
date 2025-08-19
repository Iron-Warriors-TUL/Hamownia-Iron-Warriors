"""gpio.py
This module provides functionality to handle GPIO encoder input for RPM measurement."""

from typing import Optional
import time

from logger import Logger
from mocks import MockGPIO
import settings

try:
    import RPi.GPIO as GPIO
except ImportError:
    from mocks import GPIO
import threading
import time


class GPIOHandler:
    """A class to handle GPIO encoder input for RPM measurement."""

    last_time_ns: Optional[int] = None
    pulse_count: int = 0

    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(settings.ENCODER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            settings.ENCODER_PIN, GPIO.FALLING, callback=self._encoder_callback
        )
        if isinstance(GPIO, MockGPIO):  # Start the simulation thread
            self.simulation_thread = threading.Thread(
                target=self.simulate_rpm_changes, daemon=True
            )
            self.simulation_thread.start()

    def simulate_rpm_changes(self):
        """Simulate changing RPM values over 60 seconds."""
        start_time = time.time()
        total_duration = 60

        while True:
            elapsed = time.time() - start_time
            if elapsed >= total_duration:
                break

            if elapsed < 15:
                target_rpm = (elapsed / 15) * 4000
            elif elapsed < 30:
                target_rpm = 4000 - ((elapsed - 15) / 15) * 2000
            elif elapsed < 45:
                target_rpm = 2000 + ((elapsed - 30) / 15) * 1000
            else:
                target_rpm = 3000 - ((elapsed - 45) / 15) * 3000

            if target_rpm > 0:
                interval_seconds = 60 / target_rpm

                if isinstance(GPIO, MockGPIO):
                    GPIO.trigger(settings.ENCODER_PIN)

                time.sleep(interval_seconds)
            else:
                time.sleep(0.1)

    def _encoder_callback(self, _):
        """Callback function for encoder input."""
        now_ns = time.time_ns()
        if self.last_time_ns:
            delta_ns: int = now_ns - self.last_time_ns
            if delta_ns > settings.MIN_DELTA_NS:
                self.pulse_count += 1
                self.logger.enque_data(self.pulse_count, delta_ns, now_ns)
        self.last_time_ns = now_ns
