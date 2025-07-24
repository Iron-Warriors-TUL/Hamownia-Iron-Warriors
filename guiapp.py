"""guiapp.py
This module provides a simple GUI application to display RPM, Torque, and Power data."""

import tkinter as tk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import settings
from logger import Logger


class GuiApp:
    """A simple GUI application to display RPM, Torque, and Power data."""

    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.root = tk.Tk()
        self.root.title("Iron Warriors Hamownia")
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH)
        self.create_widgets()
        self.fig_setup()
        self.update_loop()

    def create_widgets(self):
        """Create the main widgets for the GUI."""
        self.label_rpm = tk.Label(self.main_frame, text="RPM: 0")
        self.label_rpm.pack()
        self.label_torque = tk.Label(self.main_frame, text="Torque: 0 Nm")
        self.label_torque.pack()
        self.label_power = tk.Label(self.main_frame, text="Power: 0 W")
        self.label_power.pack()

        self.toggle_button = tk.Button(
            self.main_frame, text="Start Logging", command=self.toggle_logging
        )
        self.toggle_button.pack()

    def fig_setup(self):
        """Set up the matplotlib figure and canvas."""
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

    def toggle_logging(self):
        """Toggle the logging state."""
        if self.logger.recording_active:
            self.logger.recording_active = False
            self.toggle_button.config(text="Start Logging")
        else:
            self.logger.clean_data()
            self.logger.recording_active = True
            self.toggle_button.config(text="Stop Logging")

    def update_loop(self):
        """Update the GUI with the latest data."""
        if self.logger.rpm_log:
            self.label_rpm.config(text=f"RPM: {self.logger.rpm_log[-1]:.2f}")
            self.label_torque.config(
                text=f"Torque: {self.logger.torque_log[-1]:.3f} Nm"
            )
            self.label_power.config(text=f"Power: {self.logger.power_log[-1]:.2f} W")

        self.ax.clear()
        self.ax.set_title("Torque and Power vs RPM (last 30 seconds)")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("RPM")
        if self.logger.timestamp_log:
            start = self.logger.timestamp_log[-1] - 30
            x_vals = [
                t - self.logger.timestamp_log[0]
                for t in self.logger.timestamp_log
                if t >= start
            ]
            y_vals = self.logger.rpm_log[-len(x_vals) :]
            self.ax.plot(x_vals, y_vals, label="RPM", color="blue")
        self.canvas.draw()
        self.root.after(int(settings.LOG_INTERVAL * 1000), self.update_loop)

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()
