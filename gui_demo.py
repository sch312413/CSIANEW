import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import Calendar

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def ensure_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        with open(SCHEMA_PATH) as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Must run before importing genetic3 -- that module queries the database
# at import time (DAY_AVAIL_SLOTS = day_unavailable()), so the tables need
# to already exist by the time the import statement runs. Same ordering
# issue as in the Flask version's app.py.
ensure_db()

import genetic3  # unmodified copy of your real genetic3.py, sitting next to this file

root = tk.Tk()

class SmartCalendarApp:
    def __init__(self, root):
        self.root = root
        root.title("Smart Calendar")
        root.geometry = ("1050x650")

        self.all_itms = []
        self.toolbar(root)
        self.calendar(root)
        self.bottom_bar(root)
        # self.refresh(root)

    def toolbar(self, root):
        toolbar = ttk.Frame(root)
        toolbar.pack(fill="x", padx = 10, pady = 10)

        add_task = ttk.Button(toolbar, text="+ Add task", command=self.task_popup).pack(side="left", padx = 5)
        add_event = ttk.Button(toolbar, text="+ Add event", command=self.event_popup).pack(side="left", padx = 5)
        add_session = ttk.Button(toolbar, text="+ Add work session").pack(side="left", padx = 5)
        preferences = ttk.Button(toolbar, text="Settings").pack(side="left", padx = 5)

    def bottom_bar(self, root):
        bottombar = ttk.Frame(root)
        bottombar.pack(fill="x", padx = 10, pady = 10)
        add_event = ttk.Button(bottombar, text="Generate smart schedule").pack(side="left", padx = 5)
        add_session = ttk.Button(bottombar, text="Accept selected").pack(side="left", padx = 5)
        preferences = ttk.Button(bottombar, text="Delete selected").pack(side="left", padx = 5)


    def calendar(self, root):
        container = ttk.Frame(root)
        container.pack(fill="both", expand=True, padx=10, pady=5)
        self.cal = Calendar(
            container, 
            selectmode = "day", 
            date_pattern="yyyy-mm-dd", 
            headerforeground = "#000000",
            normalbackground = "#FFFFFF",
            weekendbackground = "#FFFFA9",
            selectbackground = "#FF80B7"
            )

        self.cal.pack(side="left", fill="both", expand=True, padx=(0, 10))
        # self.cal.bind("<DateSelect>", self.date_selected)

        right = ttk.Frame(container)
        right.pack(side="left", fill="both")



    def task_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add a task")

        ttk.Label(popup, text="Title").grid(row=0, column=0, padx=10, pady=10)
        title_entry = ttk.Entry(popup, width=30).grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(popup, text="Task due date (YYYY-MM-DDTHH:MM)").grid(row=1, column=0, padx=10, pady=10)
        due_entry = ttk.Entry(popup, width=30).grid(row=1, column=1, padx=10, pady=5) 

        ttk.Label(popup, text="Minutes of work required").grid(row=2, column=0, padx=10, pady=10)
        work_entry = ttk.Entry(popup, width=30).grid(row=2, column=1, padx=10, pady=5) 

    def event_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add an event")

        ttk.Label(popup, text="Title").grid(row=0, column=0, padx=10, pady=10)
        title_entry = ttk.Entry(popup, width=30).grid(row=0, column=1, padx=10, pady=5)

        whole_day_var = tk.IntVar()
        ttk.Checkbutton(popup, text="Whole day event", variable=whole_day_var).grid(row=1, column=0, padx=5, pady=10)
    
        if whole_day_var == 0:
            recurrence = tk.Frame(self.root)
            ttk.Label(popup, text="Recurrence").grid(row=0, column=0, padx=10, pady=10)
            days = ["Mon", "Tues", "Wed", "Thu", "Fri", "Sat", "Sun"]
            days_checked = []
            for i in range(days):
                curr = tk.IntVar()
                ttk.Checkbutton(recurrence, text=days[i], variable=curr).grid(row=1, column=i, padx=1, pady=1)
                days_checked.append(curr)

            ttk.Label(popup, text="Event start date (YYYY-MM-DDTHH:MM)").grid(row=1, column=0, padx=10, pady=10)
            due_entry = ttk.Entry(popup, width=30).grid(row=1, column=1, padx=10, pady=5) 

            ttk.Label(popup, text="Event end date (YYYY-MM-DDTHH:MM)").grid(row=1, column=0, padx=10, pady=10)
            due_entry = ttk.Entry(popup, width=30).grid(row=1, column=1, padx=10, pady=5) 
        else:
            ttk.Label(popup, text="Event start date (YYYY-MM-DD)").grid(row=1, column=0, padx=10, pady=10)
            due_entry = ttk.Entry(popup, width=30).grid(row=1, column=1, padx=10, pady=5) 

            ttk.Label(popup, text="Event end date (YYYY-MM-DD)").grid(row=1, column=0, padx=10, pady=10)
            due_entry = ttk.Entry(popup, width=30).grid(row=1, column=1, padx=10, pady=5)          

            


calendar = SmartCalendarApp(root)
style = ttk.Style()
style.theme_use("clam")
root.mainloop()