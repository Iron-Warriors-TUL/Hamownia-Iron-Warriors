ENCODER_PIN: int = 16
MOMENT_OF_INERTIA: float = 0.038  # kg·m²
MAX_RPM: int = 9000  # max RPM for safety
LOG_INTERVAL: float = 0.1  # seconds
MIN_DELTA_NS: int = 6  # 6_000_000  # ~10000 RPM
LOG_FILE: str = "log.csv"
OSCILLATION_REMOVAL_ALPHA: float = (
    0.01  # this is how much you allow for oscillations in plotting
)
WINDOW_SIZE_NS: int = 500_000_000  # 100 ms window
