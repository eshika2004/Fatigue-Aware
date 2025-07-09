import tkinter as tk
from tkinter import messagebox
import threading
import os
import webbrowser
import json
import shutil

from recorder import record_for_5_minutes
from fatigue_monitor import start_monitoring

monitor_thread = None
stop_event = threading.Event()

record_stop_event = threading.Event()
record_thread = None


def start_recording_thread():
    global record_thread, record_stop_event
    record_stop_event.clear()
    status_label.config(text="Recording started...")

    def record_and_notify():
        video, log = record_for_5_minutes(record_stop_event)
        status_label.config(text="Recording stopped.")
        messagebox.showinfo("Recording Done", f"Saved:\n{video}\n{log}")

    record_thread = threading.Thread(target=record_and_notify)
    record_thread.start()


def stop_recording():
    if record_thread and record_thread.is_alive():
        record_stop_event.set()
        status_label.config(text="Stopping recording...")
    else:
        messagebox.showinfo("Info", "Recording is not running.")


def start_monitoring_thread():
    stop_event.clear()
    threading.Thread(target=start_monitoring, args=(stop_event,)).start()
    status_label.config(text="Monitoring started...")


def stop_monitoring():
    stop_event.set()
    status_label.config(text="Monitoring stopped.")


def open_recordings_folder():
    path = os.path.abspath("recordings")
    if not os.path.exists(path):
        os.makedirs(path)
    webbrowser.open(path)


def view_baseline_info():
    json_file = "recordings/baseline.json"
    if os.path.exists(json_file):
        with open(json_file, "r") as f:
            data = json.load(f)
            info = (
                f"Blink Count: {data['blink_count']}\n"
                f"Duration: {data['duration_minutes']} minutes\n"
                f"Blinks per Minute: {data['blinks_per_minute']}\n"
                f"Recorded at: {data['timestamp']}"
            )
            messagebox.showinfo("Baseline Info", info)
    else:
        messagebox.showwarning("No Data", "No baseline calibration data found.")


def delete_calibration_data():
    folder = "recordings"
    if os.path.exists(folder):
        confirm = messagebox.askyesno("Delete", "Are you sure you want to delete all calibration data?")
        if confirm:
            shutil.rmtree(folder)
            os.makedirs(folder)
            messagebox.showinfo("Deleted", "Calibration data deleted.")
    else:
        messagebox.showinfo("No Data", "No calibration data found.")


# GUI Setup
root = tk.Tk()
root.title("Fatigue Detection System")
root.geometry("360x450")

tk.Label(root, text="Welcome!", font=("Helvetica", 18)).pack(pady=10)

tk.Button(root, text="🎥 Start 5-Min Recording", command=start_recording_thread, width=30, bg="blue", fg="white").pack(
    pady=6)
tk.Button(root, text="🛑 Stop Recording", command=stop_recording, width=30, bg="orange", fg="white").pack(pady=6)
tk.Button(root, text="🧠 Start Monitoring", command=start_monitoring_thread, width=30, bg="green", fg="white").pack(
    pady=6)
tk.Button(root, text="🛑 Stop Monitoring", command=stop_monitoring, width=30, bg="red", fg="white").pack(pady=6)
tk.Button(root, text="📁 View Saved Recordings", command=open_recordings_folder, width=30).pack(pady=6)
tk.Button(root, text="📊 View Baseline Info", command=view_baseline_info, width=30).pack(pady=6)
tk.Button(root, text="🗑️ Delete Calibration Data", command=delete_calibration_data, width=30).pack(pady=6)

status_label = tk.Label(root, text="Status: Idle", fg="gray")
status_label.pack(pady=15)


def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        stop_event.set()  # Signal monitoring thread to stop
        record_stop_event.set()  # Signal recording thread to stop
        root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
