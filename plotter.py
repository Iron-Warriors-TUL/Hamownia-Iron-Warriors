"""plotter.py
This module provides functionality to generate plots for RPM, Torque, and Power data."""

from typing import List, Tuple

import matplotlib.pyplot as plt
import settings


class Plotter:
    """A class to handle plotting of RPM, Torque, and Power data."""

    @staticmethod
    def generate_summary_plot(
        rpm_log: List[float], torque_log: List[float], power_log: List[float]
    ) -> None:
        """Generates a summary plot of RPM, Torque, and Power."""
        if not rpm_log or not torque_log or not power_log:
            print("No data to plot.")
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        clean_rpm_log, clean_torque_log, clean_power_log = Plotter.clean_data(
            rpm_log, torque_log, power_log
        )
        color = "tab:blue"
        ax.scatter(
            clean_rpm_log, clean_torque_log, color=color, label="Torque (Nm)", s=10
        )
        ax.scatter(
            clean_rpm_log, clean_power_log, color="tab:orange", label="Power (W)", s=10
        )
        ax.set_title("Torque and Power vs RPM")
        ax.set_xlabel("RPM")
        ax.set_ylabel("Torque (Nm) / Power (W)")
        ax.set_xlim([0, settings.MAX_RPM])
        fig.tight_layout()
        fig.savefig("torque_power_vs_rpm.png")
        plt.close(fig)

    @staticmethod
    def clean_data(
        rpm_log: List[float], torque_log: List[float], power_log: List[float]
    ) -> Tuple[List[float], List[float], List[float]]:
        """Cleans the data by removing negative values and normalizing power."""
        clean_rpm_log: List[float] = []
        clean_torque_log: List[float] = []
        clean_power_log: List[float] = []
        for r, t, p in zip(rpm_log, torque_log, power_log):
            if t >= 0 and p >= 0:
                clean_rpm_log.append(r)
                clean_torque_log.append(t)
                clean_power_log.append(p / 1000)

        return clean_rpm_log, clean_torque_log, clean_power_log
