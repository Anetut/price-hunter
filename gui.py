import json
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox

from dotenv import dotenv_values

from price_hunter import load_json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

STARTUP_FILE = os.path.join(os.getenv("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup\PriceHunter.bat")
# pythonw is python without the black console window, good for running in the background
PYTHONW = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
SCRIPT = os.path.abspath("price_hunter.py")

EMAIL_FIELDS = [
    ("EMAIL_ADDRESS", "Your Gmail"),
    ("EMAIL_PASSWORD", "App password"),
    ("EMAIL_TO", "Send alerts to"),
]

ALERT_FIELDS = [
    ("name", "Name"),
    ("url", "Product link"),
    ("selector", "Price selector"),
]


# ---------- email settings ----------

def save_email():
    with open(".env", "w") as f:
        for name, label in EMAIL_FIELDS:
            f.write(f"{name}={email_entries[name].get()}\n")
    messagebox.showinfo("Saved", "Email settings saved!")


# ---------- alerts ----------

def save_alerts():
    with open("alerts.json", "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)


def refresh_list():
    alert_list.delete(0, tk.END)
    for alert in alerts:
        alert_list.insert(tk.END, f"{alert['name']}  -  {alert['url']}")


def read_form():
    alert = {
        "name": alert_entries["name"].get(),
        "url": alert_entries["url"].get(),
        "selector": alert_entries["selector"].get(),
    }
    for name, label in ALERT_FIELDS:
        if not alert[name]:
            messagebox.showerror("Oops", f"{label} can't be empty")
            return None
    return alert


def add_alert():
    alert = read_form()
    if alert:
        alerts.append(alert)
        save_alerts()
        refresh_list()


def update_alert():
    selected = alert_list.curselection()
    if not selected:
        messagebox.showinfo("Update", "First click an alert in the list")
        return
    alert = read_form()
    if alert:
        alerts[selected[0]] = alert
        save_alerts()
        refresh_list()


def delete_alert():
    selected = alert_list.curselection()
    if not selected:
        messagebox.showinfo("Delete", "First click an alert in the list")
        return
    del alerts[selected[0]]
    save_alerts()
    refresh_list()


def alert_clicked(event):
    # put the clicked alert in the form so you can change it
    selected = alert_list.curselection()
    if not selected:
        return
    alert = alerts[selected[0]]
    for name, label in ALERT_FIELDS:
        alert_entries[name].delete(0, tk.END)
        alert_entries[name].insert(0, str(alert[name]))


def check_all_now():
    result = subprocess.run([sys.executable, "price_hunter.py"], capture_output=True, text=True)
    messagebox.showinfo("Result", result.stdout + result.stderr or "No alerts yet")


# ---------- check when pc starts ----------

def startup_on():
    # everything in the windows Startup folder runs when you log in
    # it runs price_hunter.py once in the background, and then it closes
    with open(STARTUP_FILE, "w") as f:
        f.write(f'start "" "{PYTHONW}" "{SCRIPT}" --startup\n')
    refresh_startup_status()
    messagebox.showinfo("Startup", "Your alerts will be checked every time the PC starts")


def startup_off():
    if os.path.exists(STARTUP_FILE):
        os.remove(STARTUP_FILE)
    refresh_startup_status()
    messagebox.showinfo("Startup", "Alerts will not be checked when the PC starts")


def refresh_startup_status():
    if os.path.exists(STARTUP_FILE):
        startup_status.config(text="Check when PC starts: ON", fg="green")
    else:
        startup_status.config(text="Check when PC starts: OFF", fg="red")


# ---------- the window ----------

window = tk.Tk()
window.title("Price Hunter")

# email settings
email_frame = tk.LabelFrame(window, text="Email settings", padx=5, pady=5)
email_frame.pack(fill="x", padx=10, pady=5)

saved = dotenv_values(".env")
email_entries = {}
for row, (name, label) in enumerate(EMAIL_FIELDS):
    tk.Label(email_frame, text=label).grid(row=row, column=0, sticky="w")
    entry = tk.Entry(email_frame, width=50)
    if name == "EMAIL_PASSWORD":
        entry.config(show="*")
    entry.insert(0, saved.get(name) or "")
    entry.grid(row=row, column=1, padx=5, pady=2)
    email_entries[name] = entry
tk.Button(email_frame, text="Save email settings", command=save_email).grid(row=len(EMAIL_FIELDS), column=1, sticky="e", pady=5)

# alerts
alerts_frame = tk.LabelFrame(window, text="Alerts", padx=5, pady=5)
alerts_frame.pack(fill="x", padx=10, pady=5)

# exportselection=False so the list keeps its selection when you type in the form
alert_list = tk.Listbox(alerts_frame, width=80, height=6, exportselection=False)
alert_list.grid(row=0, column=0, columnspan=2, pady=5)
alert_list.bind("<<ListboxSelect>>", alert_clicked)

alert_entries = {}
for row, (name, label) in enumerate(ALERT_FIELDS, start=1):
    tk.Label(alerts_frame, text=label).grid(row=row, column=0, sticky="w")
    entry = tk.Entry(alerts_frame, width=60)
    entry.grid(row=row, column=1, padx=5, pady=2)
    alert_entries[name] = entry

buttons = tk.Frame(alerts_frame)
buttons.grid(row=len(ALERT_FIELDS) + 1, column=0, columnspan=2, pady=5)
tk.Button(buttons, text="Add new", command=add_alert).pack(side="left", padx=3)
tk.Button(buttons, text="Update selected", command=update_alert).pack(side="left", padx=3)
tk.Button(buttons, text="Delete selected", command=delete_alert).pack(side="left", padx=3)
tk.Button(buttons, text="Check all now", command=check_all_now).pack(side="left", padx=3)

# check when pc starts
startup_frame = tk.LabelFrame(window, text="Check when PC starts", padx=5, pady=5)
startup_frame.pack(fill="x", padx=10, pady=5)

# the startup folder trick only exists on windows
if sys.platform == "win32":
    startup_status = tk.Label(startup_frame, text="")
    startup_status.pack(side="left")
    tk.Button(startup_frame, text="Turn off", command=startup_off).pack(side="right", padx=3)
    tk.Button(startup_frame, text="Turn on", command=startup_on).pack(side="right", padx=3)
else:
    tk.Label(startup_frame, text="This only works on Windows").pack(side="left")

alerts = load_json("alerts.json", [])
refresh_list()
if sys.platform == "win32":
    refresh_startup_status()

window.mainloop()
