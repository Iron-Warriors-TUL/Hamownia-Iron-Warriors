from typing import Optional
import time
import settings
from logger import Logger
try:
    import RPi.GPIO as GPIO
except ImportError:
    pass

class GPIOHandler:

    _last_time_ns: Optional[int] = None
    _pulse_count: int = 0
    _logger: Logger = Logger()

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(settings.ENCODER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(settings.ENCODER_PIN, GPIO.RISING, callback=self._encoder_callback)

    def _encoder_callback(self, _):
        now_ns: int = time.time_ns()
        if self._last_time_ns is not None:
            delta_ns: int = now_ns - self._last_time_ns
            if delta_ns >= settings.MIN_DELTA_NS:
                self._pulse_count += 1
                self._logger.enqueue_data(self._pulse_count, delta_ns, now_ns)
        else:
            self._last_time_ns = now_ns