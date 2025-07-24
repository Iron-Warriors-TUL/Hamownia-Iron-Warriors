"""main.py"""

from guiapp import GuiApp
from logger import Logger
from gpio import GPIOHandler


def main():
    """Main function to run the GUI application."""
    logger = Logger()
    _ = GPIOHandler(logger)  # Initialization handles everything needed for GPIO
    gui_app = GuiApp(logger)

    try:
        gui_app.root.mainloop()
    except KeyboardInterrupt:
        print("Exiting application...")


if __name__ == "__main__":
    main()
