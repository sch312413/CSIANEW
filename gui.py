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

ensure_db()

DAYS = ["Mon", "Tues", "Wed", "Thu", "Fri", "Sat", "Sun"]
import genetic3
class SmartCalendarApp:
    def __init__(self, root):
        self.root = root
        root.title("Smart Calendar")
        root.geometry("1960x1000")

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
        window = ttk.Button(toolbar, text="+ Daily unavailable window", command=self.preferences).pack(side="left", padx = 5)
        settings = ttk.Button(toolbar, text="Settings", command=self.settings).pack(side="left", padx = 5)

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
            selectbackground = "#FF80B7", 
            width=600, 
            height=650
            )
        
        self.date_selected = self.cal.selection_get()
        self.cal.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.cal.bind("<<CalendarSelected>>", self.date_selected)

        right = ttk.Frame(container)
        right.pack(side="left", fill="both")

        right_title = ttk.Label(right, text="Items for the day: ").pack()
        task_column = ("Title", 'Time', "Type", "Status")
        self.day_list = ttk.Treeview(right, columns=task_column, show="headings", height=15)

        my_date = self.cal.selection_get()
        tasks, work_seshs, events = self.get_all_information()
        for task in tasks:
            if task["date"] == my_date:
                self.day_list.insert("", "end", values=(task["title"], task["time"], task["status"], task["type"]))        

        task_column = ("Title", 'Time', "Type", "Status")
        self.day_list = ttk.Treeview(right, columns=task_column, show="headings", height=15)
        for sesh in work_seshs:
            if task["date"] == my_date:
                # "Task name": row["title"], "date": start_dt.date(), "Start time": start_dt.time(), "End time": end_dt.time(), "status": row["status_now"]
                self.day_list.insert("", "end", values=(sesh["title"], sesh["Start time"], sesh["End time"], sesh["type"], sesh["status"]))   

                     

    def get_all_information(self):
        conn = get_db()
        tasks, work_sesh, events = [], [], []
        for row in conn.execute("SELECT title, due_time, status_now FROM tasks"):
            dt = datetime.fromisoformat(row["due_time"])
            tasks.append({"title": row["title"], "date": dt.date(), "due time": dt.time(), "status": row["status_now"], "type": row["status now"]})
        for row in conn.execute("SELECT task_id, start_time, end_time, status_now FROM work_session"):
            start_dt = datetime.fromisoformat(row["start_time"])
            end_dt = datetime.fromisoformat(row["end_time"])
            conn.execute(f"SELECT title FROM tasks WHERE task_id = f{row["task_id"]}")
            work_sesh.append({"Task name": row["title"], "date": start_dt.date(), "Start time": start_dt.time(), "End time": end_dt.time(), "status": row["status_now"]})
        for row in conn.execute("SELECT event_id, title, starting_datetime, ending_datetime FROM events"):
            dt_start = datetime.fromisoformat(row["starting_datetime"])
            dt_end = datetime.fromisoformat(row["ending_datetime"])
            events.append({"title": row["title"], "date": dt_start.date(), "start_time": dt_start.time(), "end_time": dt_end.time(), "status": '-', "type": "Event"})
        return tasks, work_sesh, events 

    def task_popup(self):
        self.t_popup = tk.Toplevel(self.root)
        self.t_popup.title("Add a task")

        # Title 
        title_text = ttk.Label(self.t_popup, text="Title")
        title_text.grid(row=0, column=0, padx=10, pady=10)
        self.t_title_entry = ttk.Entry(self.t_popup, width=30)
        self.t_title_entry.grid(row=0, column=1, padx=10, pady=5)

        # Due date 
        due_text = ttk.Label(self.t_popup, text="Task due date (YYYY-MM-DDTHH:MM)")
        due_text.grid(row=1, column=0, padx=10, pady=10)
        self.t_due_entry = ttk.Entry(self.t_popup, width=30)
        self.t_due_entry.grid(row=1, column=1, padx=10, pady=5) 

        # Work minute 
        minutes_text = ttk.Label(self.t_popup, text="Minutes of work required")
        minutes_text.grid(row=2, column=0, padx=10, pady=10)
        self.t_work_entry = ttk.Entry(self.t_popup, width=30)
        self.t_work_entry.grid(row=2, column=1, padx=10, pady=5) 

        self.t_submit = ttk.Button(self.t_popup, text="Submit", command=self.submit_task)
        self.t_submit.grid(row=3, column=0, padx=10, pady=10)

    # submit 
    def submit_task(self):
        title = self.t_title_entry.get().strip()
        due = self.t_due_entry.get().strip()
        minutes = self.t_work_entry.get().strip()

        if not title or not due or not minutes:
            messagebox.showwarning("Error", "Please fill in all text fields!")
            return 

        try: check = datetime.fromisoformat(due)
        except: check = -1 

        try: minutes = int(minutes)
        except: minutes = -1

        if check == -1:
            messagebox.showwarning("Error", "Please follow the exact date format!")
            return            
        if minutes < 0:
            messagebox.showwarning("Error", "Please enter a valid working minute!")
            return   

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
        "INSERT INTO tasks (title, due_time, total_minutes, scheduled_minute, status_now) " \
        "VALUES (?, ?, ?, 0, 'active')", 
        (title, due, minutes)
        )     
        conn.commit()
        conn.close()
        self.t_popup.destroy()

    # event popup 
    def event_popup(self):
        self.e_popup = tk.Toplevel(self.root)
        self.e_popup.title("Add an event")

        ttk.Label(self.e_popup, text="Title").grid(row=0, column=0, padx=10, pady=10)
        self.e_title_entry = ttk.Entry(self.e_popup, width=30)
        self.e_title_entry.grid(row=1, column=0, padx=10, pady=5)

        ttk.Label(self.e_popup, text="Event Type").grid(row=2, column=0, padx=10, pady=10)
        self.e_type_entry = ttk.Entry(self.e_popup, width=30)
        self.e_type_entry.grid(row=3, column=0, padx=10, pady=5)

        self.whole_day_var = tk.IntVar()
        self.whole_day_check = ttk.Checkbutton(self.e_popup, text="Whole day event", variable=self.whole_day_var, command=self.on_toggle)
        self.whole_day_check.grid(row=4, column=0, padx=5, pady=10)

        self.whole_day_events = ttk.Frame(self.e_popup)
        self.non_whole_day = ttk.Frame(self.e_popup)

        # non whole day
        self.recurrence = tk.Frame(self.non_whole_day)
        self.recurrence.grid(row=0, column=0, padx=10, pady=5)
        ttk.Label(self.recurrence, text="Recurrence").grid(row=0, column=0, padx=10, pady=10)
        
        self.days_button = {}
        self.days_checked = []
        for i in range(len(DAYS)):
            self.days_checked.append(tk.IntVar())
            self.days_button[DAYS[i]] = ttk.Checkbutton(self.recurrence, text=DAYS[i], variable=self.days_checked[i])
            self.days_button[DAYS[i]].grid(row=1, column=i, padx=10, pady=10)

        ttk.Label(self.non_whole_day, text="Event start date (YYYY-MM-DDTHH:MM)").grid(row=1, column=0, padx=10, pady=10)
        self.e_start_datetime = ttk.Entry(self.non_whole_day, width=30)
        self.e_start_datetime.grid(row=1, column=1, padx=10, pady=5) 

        ttk.Label(self.non_whole_day, text="Event end date (YYYY-MM-DDTHH:MM)").grid(row=2, column=0, padx=10, pady=10)
        self.e_end_datetime = ttk.Entry(self.non_whole_day, width=30)
        self.e_end_datetime.grid(row=2, column=1, padx=10, pady=5) 

        self.e_submit = ttk.Button(self.non_whole_day, text="Submit", command=self.submit_e_non)
        self.e_submit.grid(row=3, column=0, padx=10, pady=10)  

        # whole day
        ttk.Label(self.whole_day_events, text="Event start date (YYYY-MM-DD)").grid(row=0, column=0, padx=10, pady=10)
        self.e_start_date = ttk.Entry(self.whole_day_events, width=30)
        self.e_start_date.grid(row=0, column=1, padx=10, pady=5) 

        ttk.Label(self.whole_day_events, text="Event end date (YYYY-MM-DD)").grid(row=1, column=0, padx=10, pady=10)
        self.e_end_date = ttk.Entry(self.whole_day_events, width=30)
        self.e_end_date.grid(row=1, column=1, padx=10, pady=5)   

        self.e_submit = ttk.Button(self.whole_day_events, text="Submit", command=self.submit_e_whole)
        self.e_submit.grid(row=2, column=0, padx=10, pady=10)  

        self.on_toggle()

    def on_toggle(self):
        if self.whole_day_var.get()==0:
            self.whole_day_events.grid_remove()
            self.non_whole_day.grid(row=0,column=2, sticky="s", rowspan=5)
        else:
            self.non_whole_day.grid_remove()
            self.whole_day_events.grid(row=0,column=2, sticky="s", rowspan=5)   

    def submit_e_whole(self):
        title = self.e_title_entry.get().strip()
        type = self.e_type_entry.get().strip()
        start = self.e_start_date.get().strip()
        end = self.e_end_date.get().strip()
        start +="T00:00"
        end += "T00:00"

        if not title or not start or not end or not type:
            messagebox.showwarning("Error", "Please fill in all text fields!")
            return 

        try: check_start = datetime.fromisoformat(start)
        except: check_start = -1 
        try: check_end = datetime.fromisoformat(end)
        except: check_end = -1 

        if check_start == -1 or check_end == -1:
            messagebox.showwarning("Error", "Please follow the exact date format!")
            return  

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
        "INSERT INTO events (title, event_type, whole_day, recurrence, starting_datetime, ending_datetime) " \
        "VALUES (?, ?, 1, ?, ?, ?)", 
        (title, type, None, start, end)
        )     
        conn.commit()
        conn.close()
        self.e_popup.destroy()      

    def submit_e_non(self):
        title = self.e_title_entry.get().strip()
        type = self.e_type_entry.get().strip()
        start = self.e_start_datetime.get().strip()
        end = self.e_end_datetime.get().strip()

        if not title or not start or not end or not type:
            messagebox.showwarning("Error", "Please fill in all text fields!")
            return 

        recur = ''
        for i in range(len(DAYS)):
            if self.days_checked[i].get() == 1:
                recur+=f"{DAYS[i]},"
        if not recur:
            recur = None

        try: check_start = datetime.fromisoformat(start)
        except: check_start = -1 
        try: check_end = datetime.fromisoformat(end)
        except: check_end = -1 

        if check_start == -1 or check_end == -1:
            messagebox.showwarning("Error", "Please follow the exact date format!")
            return  

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
        "INSERT INTO events (title, event_type, whole_day, recurrence, starting_datetime, ending_datetime) " \
        "VALUES (?, ?, 0, ?, ?, ?)", 
        (title, type, recur, start, end)
        )     
        conn.commit()
        conn.close()
        self.e_popup.destroy() 

    def settings(self):
        self.w_popup = tk.Toplevel(self.root)
        self.w_popup.title("Preferences")

        # Settings
        ttk.Label(self.w_popup, text="Settings").grid(row=0, column=0, padx=10, pady=10)

        # max working 
        ttk.Label(self.w_popup, text="Maximum working minute per day").grid(row=1, column=0, padx=10, pady=10)
        self.w_daylim_entry = ttk.Entry(self.w_popup, width=30)
        self.w_daylim_entry.grid(row=1, column=1, padx=10, pady=5)

        # min break 
        ttk.Label(self.w_popup, text="Minimum break between work sessions").grid(row=2, column=0, padx=10, pady=10)
        self.w_minb_entry = ttk.Entry(self.w_popup, width=30)
        self.w_minb_entry.grid(row=2, column=1, padx=10, pady=5)

        # max session  
        ttk.Label(self.w_popup, text="Maximum session minutes").grid(row=3, column=0, padx=10, pady=10)
        self.w_maxs_entry = ttk.Entry(self.w_popup, width=30)
        self.w_maxs_entry.grid(row=3, column=1, padx=10, pady=5)

        # submit 
        self.w_submit_s = ttk.Button(self.w_popup, text="Submit settings", command=self.settings_submit)
        self.w_submit_s.grid(row=4, column=0, padx=10, pady=5)     

    def settings_submit(self):
        max_work = self.w_daylim_entry.get().strip()
        min_break = self.w_minb_entry.get().strip()
        max_sesh = self.w_maxs_entry.get().strip()

        if not max_work or not min_break or not max_sesh:
            messagebox.showwarning("Error", "Please fill in all text fields!")
            return 

        try: max_work = int(max_work) 
        except: 
            messagebox.showwarning("Error", "'Maximum working minute' must be an integer!") 
            return 

        try: min_break = int(min_break) 
        except: 
            messagebox.showwarning("Error", "'Minimum break between work sessions' must be an integer!") 
            return 

        try: max_sesh = int(max_sesh) 
        except: 
            messagebox.showwarning("Error", "'Maximum session minutes' must be an integer!") 
            return 

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
        "UPDATE settings "
        "SET settings_id = 1, max_working = ?, min_break = ?, max_session_minutes = ?", 
        (max_work, min_break, max_sesh)
        )     
        conn.commit()
        conn.close()
        self.w_popup.destroy()       

    def preferences(self):
        # unavailable windows
        self.s_popup = tk.Toplevel(self.root)
        self.s_popup.title("Settings")
        ttk.Label(self.s_popup, text="Daily unavailable time window").grid(row=0, column=0, padx=10, pady=10)

        # title
        ttk.Label(self.s_popup, text="Title").grid(row=1, column=0, padx=10, pady=10)
        self.w_title_entry = ttk.Entry(self.s_popup, width=30)
        self.w_title_entry.grid(row=1, column=1, padx=10, pady=5)

        # start time
        ttk.Label(self.s_popup, text="Start time (HH:mm)").grid(row=2, column=0, padx=10, pady=10)
        self.w_start_entry = ttk.Entry(self.s_popup, width=30)
        self.w_start_entry.grid(row=2, column=1, padx=10, pady=5)       
    
        # end time
        ttk.Label(self.s_popup, text="End time (HH:mm)").grid(row=3, column=0, padx=10, pady=10)
        self.w_end_entry = ttk.Entry(self.s_popup, width=30)
        self.w_end_entry.grid(row=3, column=1, padx=10, pady=5) 

        # submit 
        self.w_submit_u = ttk.Button(self.s_popup, text="Submit window", command=self.preferences_submit)
        self.w_submit_u.grid(row=4, column=0, padx=10, pady=5)   

    def preferences_submit(self):
        title = self.w_title_entry.get().strip()
        start = self.w_start_entry.get().strip()
        end = self.w_end_entry.get().strip()

        if not title or not start or not end:
            messagebox.showwarning("Error", "Please fill in all text fields!")
            return 

        try: 
            check_start = datetime.strptime(start, "%H:%M").time() 
            check_end = datetime.strptime(end, "%H:%M").time()
        except: 
            messagebox.showwarning("Error", "Please follow the time format given!") 
            return 

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
        "INSERT INTO unavailable_windows (title, unavailable_start, unavailable_end)" \
        "VALUES (?, ?, ?)", 
        (title, start, end)
        )     
        conn.commit()
        conn.close()
        self.s_popup.destroy()   

           
root = tk.Tk()
calendar = SmartCalendarApp(root)
style = ttk.Style()
style.theme_use("clam")
root.mainloop()