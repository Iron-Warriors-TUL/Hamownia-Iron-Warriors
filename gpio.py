"""gpio.py
This module provides functionality to handle GPIO encoder input for RPM measurement."""

from typing import Optional
import time

from logger import Logger
import settings
import RPi.GPIO as GPIO


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

    def _encoder_callback(self, _):
        """Callback function for encoder input."""
        now_ns = time.time_ns()
        if self.last_time_ns:
            delta_ns: int = now_ns - self.last_time_ns
            if delta_ns > settings.MIN_DELTA_NS:
                self.pulse_count += 1
                self.logger.enque_data(self.pulse_count, delta_ns, now_ns)
        self.last_time_ns = now_ns
