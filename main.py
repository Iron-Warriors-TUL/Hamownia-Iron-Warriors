"""main.py"""

import csv
from guiapp import GuiApp
from logger import Logger
from gpio import GPIOHandler
import settings
import plotter


def prepare_final_plot():
    """Prepare data for the final plot."""
    rpm_log, torque_log, power_log = [], [], []
    with open(settings.LOG_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rpm_log.append(float(row["RPM"]))
            torque_log.append(float(row["Torque(Nm)"]))
            power_log.append(float(row["Power(W)"]))
    plotter.Plotter.generate_summary_plot(rpm_log, torque_log, power_log)


def main():
    """Main function to run the GUI application."""
    logger = Logger()
    _ = GPIOHandler(logger)  # Initialization handles everything needed for GPIO
    gui_app = GuiApp(logger)

    try:
        gui_app.root.mainloop()
    except KeyboardInterrupt:
        print("Exiting application...")
    finally:
        prepare_final_plot()


if __name__ == "__main__":
    main()
