import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox

from dotenv import dotenv_values

os.chdir(os.path.dirname(os.path.abspath(__file__)))

FIELDS = [
    ("PRODUCT_URL", "Product link"),
    ("PRICE_SELECTOR", "Price selector"),
    ("TARGET_PRICE", "Target price"),
    ("EMAIL_ADDRESS", "Your Gmail"),
    ("EMAIL_PASSWORD", "App password"),
    ("EMAIL_TO", "Send alert to"),
]


def save():
    with open(".env", "w") as f:
        for name, label in FIELDS:
            f.write(f"{name}={entries[name].get()}\n")


def save_clicked():
    save()
    messagebox.showinfo("Saved", "Settings saved!")


def check_now():
    save()
    # run the price hunter script and show what it printed
    result = subprocess.run([sys.executable, "price_hunter.py"], capture_output=True, text=True)
    messagebox.showinfo("Result", result.stdout + result.stderr)


window = tk.Tk()
window.title("Price Hunter")

# fill the fields with what is already saved in .env
saved = dotenv_values(".env")
entries = {}

for row, (name, label) in enumerate(FIELDS):
    tk.Label(window, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=3)
    entry = tk.Entry(window, width=50)
    if name == "EMAIL_PASSWORD":
        entry.config(show="*")  # hide the password
    entry.insert(0, saved.get(name) or "")
    entry.grid(row=row, column=1, padx=5, pady=3)
    entries[name] = entry

tk.Button(window, text="Save", command=save_clicked).grid(row=len(FIELDS), column=0, pady=10)
tk.Button(window, text="Check now", command=check_now).grid(row=len(FIELDS), column=1, pady=10)

window.mainloop()
