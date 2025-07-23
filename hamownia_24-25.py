import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import RPi.GPIO as GPIO
import time
import datetime
import threading
import queue
import signal
import sys

# === Parameters ===
ENCODER_PIN = 16 # pin on RPi4 used
MOMENT_OF_INERTIA = 0.038  # kg·m² (constant from calculations)
MAX_RPM = 9000 # actual max is +-8000 RPM, but we use 9000 for safety
LOG_INTERVAL = 0.1  # seconds
MIN_DELTA_NS = 6_000_000  # ~10000 RPM

# === Globals ===
last_time_ns = None
pulse_count = 0
recording_active = False
start_time = None
rpm_data = []
time_data = []
rpm_log = []
torque_data = []
power_data = []
timestamp_log = []
queue_data = queue.Queue()
log_filename = datetime.datetime.now().strftime("log_%Y%m%d_%H%M%S.txt")

# === Setup GPIO ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(ENCODER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def encoder_callback(channel):
    global last_time_ns, pulse_count, recording_active

    now_ns = time.time_ns()
    if last_time_ns is not None:
        delta_ns = now_ns - last_time_ns
        if delta_ns >= MIN_DELTA_NS:
            pulse_count += 1
            queue_data.put((pulse_count, delta_ns, now_ns))
    else:
        last_time_ns = now_ns

    last_time_ns = now_ns

GPIO.add_event_detect(ENCODER_PIN, GPIO.RISING, callback=encoder_callback)

def queue_writer():
    with open(log_filename, "w") as f:
        f.write("Index\tRPM\tΔt(ns)\tω(rad/s)\tTorque(Nm)\tPower(W)\n")

        prev_omega = None
        prev_time_s = None

        while True:
            pulse_idx, delta_ns, now_ns = queue_data.get()
            if not recording_active:
                continue

            rpm = 60 * 1e9 / delta_ns
            omega = 2 * 3.1416 * rpm / 60
            now_s = now_ns / 1e9

            if prev_omega is not None and prev_time_s is not None:
                delta_omega = omega - prev_omega
                delta_t = now_s - prev_time_s
                torque = MOMENT_OF_INERTIA * delta_omega / delta_t if delta_t > 0 else 0
            else:
                torque = 0
                delta_t = 0

            power = torque * omega

            # logging data
            f.write(f"{pulse_idx}\t{rpm:.2f}\t{delta_ns}\t{omega:.2f}\t{torque:.3f}\t{power:.2f}\n")
            f.flush()

            # saving for plots
            rpm_log.append(rpm)
            torque_data.append(torque)
            power_data.append(power)
            timestamp_log.append(now_s)

            prev_omega = omega
            prev_time_s = now_s

# === GUI ===
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("RPM / Torque / Power Logger")

        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.label_rpm = ttk.Label(self.main_frame, text="RPM: 0")
        self.label_rpm.pack()
        self.label_torque = ttk.Label(self.main_frame, text="Torque: 0 Nm")
        self.label_torque.pack()
        self.label_power = ttk.Label(self.main_frame, text="Power: 0 W")
        self.label_power.pack()

        self.toggle_btn = ttk.Button(self.main_frame, text="Start", command=self.toggle_recording)
        self.toggle_btn.pack(pady=10)

        self.fig, self.ax1 = plt.subplots(figsize=(7, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.update_loop()

    def toggle_recording(self):
        global recording_active, pulse_count, rpm_log, torque_data, power_data, timestamp_log
        if not recording_active:
            pulse_count = 0
            rpm_log.clear()
            torque_data.clear()
            power_data.clear()
            timestamp_log.clear()
            self.toggle_btn.config(text="Stop")
            recording_active = True
        else:
            recording_active = False
            self.toggle_btn.config(text="Start")
            self.generate_summary_plot()

    def generate_summary_plot(self):
        if not rpm_log:
            return

        fig, ax = plt.subplots(figsize=(8, 5))
        # cleaning negative values (since they are just noise)
        clean_rpm = []
        clean_torque = []
        clean_power = []
        for r, t, p in zip(rpm_log, torque_data, power_data):
            if t >= 0 and p >= 0:
                clean_rpm.append(r)
                clean_torque.append(t)
                clean_power.append(p / 1000)

        ax.scatter(clean_rpm, clean_torque, s=10, c='red', label='Torque (Nm)')
        ax.scatter(clean_rpm, clean_power, s=10, c='blue', label='Power (kW)')

        ax.set_title("Torque & Power vs RPM")
        ax.set_xlabel("RPM")
        ax.set_ylabel("Value")
        ax.set_xlim([0, MAX_RPM])
        ax.legend()
        fig.tight_layout()
        fig.savefig("torque_power_plot.png")
        plt.close(fig)

    def update_loop(self):
        if rpm_log:
            self.label_rpm.config(text=f"RPM: {rpm_log[-1]:.2f}")
            self.label_torque.config(text=f"Torque: {torque_data[-1]:.3f} Nm")
            self.label_power.config(text=f"Power: {power_data[-1]:.1f} W")

        self.ax1.clear()
        self.ax1.set_title("RPM vs Time (last 30s)")
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("RPM")
        if timestamp_log:
            start = timestamp_log[-1] - 30
            x_vals = [t - timestamp_log[0] for t in timestamp_log if t >= start]
            y_vals = rpm_log[-len(x_vals):]
            self.ax1.plot(x_vals, y_vals, color='green')

        self.canvas.draw()
        self.root.after(int(LOG_INTERVAL * 1000), self.update_loop)

# === Start program ===
if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda sig, frame: (GPIO.cleanup(), sys.exit(0)))
    thread = threading.Thread(target=queue_writer, daemon=True)
    thread.start()
    root = tk.Tk()
    app = App(root)
    root.mainloop()
