"""
Class-based mock for RPi.GPIO so code can run on non-Raspberry Pi systems.
Lets you manually trigger pin events for testing.
"""

from typing import Callable, Dict, Optional, Tuple, Any


class MockGPIO:
    """
    Mock class for RPi.GPIO to simulate GPIO behavior.
    """

    BCM: str = "BCM"
    BOARD: str = "BOARD"

    IN: str = "IN"
    OUT: str = "OUT"
    FALLING: str = "FALLING"
    RISING: str = "RISING"
    BOTH: str = "BOTH"

    PUD_UP: str = "PUD_UP"
    PUD_DOWN: str = "PUD_DOWN"
    HIGH: int = 1
    LOW: int = 0

    def __init__(self) -> None:
        self._pin_modes: Dict[int, Tuple[str, Optional[str]]] = {}
        self._pin_values: Dict[int, int] = {}
        self._event_callbacks: Dict[int, Callable[[int], Any]] = {}
        self._mode: Optional[str] = None

    def setmode(self, mode: str) -> None:
        self._mode = mode

    def setup(self, pin: int, mode: str, pull_up_down: Optional[str] = None) -> None:
        self._pin_modes[pin] = (mode, pull_up_down)
        self._pin_values[pin] = self.HIGH

    def add_event_detect(
        self,
        pin: int,
        edge: str,
        callback: Optional[Callable[[int], Any]] = None,
        bouncetime: int = 0,
    ) -> None:
        if callback:
            self._event_callbacks[pin] = callback

    def remove_event_detect(self, pin: int) -> None:
        if pin in self._event_callbacks:
            del self._event_callbacks[pin]

    def input(self, pin: int) -> int:
        return self._pin_values.get(pin, self.HIGH)

    def output(self, pin: int, value: int) -> None:
        self._pin_values[pin] = value

    def cleanup(self, pin: Optional[int] = None) -> None:
        if pin is None:
            self._pin_modes.clear()
            self._pin_values.clear()
            self._event_callbacks.clear()
        else:
            self._pin_modes.pop(pin, None)
            self._pin_values.pop(pin, None)
            self._event_callbacks.pop(pin, None)

    def trigger(self, pin: int) -> None:
        """Simulate an input change (falling/rising edge)."""
        if pin in self._event_callbacks:
            self._event_callbacks[pin](pin)


GPIO: MockGPIO = MockGPIO()
