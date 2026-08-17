import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
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

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
import genetic2
class SmartCalendarApp:
    def __init__(self, root):
        self.root = root
        root.title("Smart Calendar")
        root.geometry("1960x1000")

        self.toolbar(root)
        self.calendar(root)
        self.bottom_bar(root)

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
        smart_schedule = ttk.Button(bottombar, text="Generate smart schedule", command=self.generate_work).pack(side="left", padx = 5)
        acccept_work = ttk.Button(bottombar, text="Accept work session", command=self.accept_selected).pack(side="left", padx = 5)
        complete_work = ttk.Button(bottombar, text="Complete task", command=self.complete_task).pack(side="left", padx = 5)
        delete = ttk.Button(bottombar, text="Delete selected item", command=self.delete_item).pack(side="left", padx = 5)

    def calendar(self, root):
        container = ttk.Frame(root)
        container.pack(fill="both", expand=True, padx=10, pady=5)

        self.left = ttk.Frame(container)
        self.left.pack(side="left")
        self.all_column = ("Title", 'Item Type', "Date")
        self.all_list = ttk.Treeview(self.left, columns=self.all_column, show="headings", height=37)
        self.all_list.pack()

        self.cal = Calendar(
            container, 
            selectmode = "day", 
            date_pattern="yyyy-mm-dd", 
            headerforeground = "#000000",
            normalbackground = "#FFFFFF",
            weekendbackground = "#FFFFA9",
            selectbackground = "#FF80B7", 
            width=600, 
            height=650)
        
        self.cal.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.cal.bind("<<CalendarSelected>>", self.date_selected)
        self.right = ttk.Frame(container)
        self.right.pack(side="left", fill="both")
        
        self.event_column = ("Title", 'Starting Time', "Ending Time")
        self.event_list = ttk.Treeview(self.right, columns=self.event_column, show="headings", height=6)
        for c in self.event_column: self.event_list.heading(c, text=c); self.event_list.column(c, width=250 if c=="Title" else 150, stretch=False)
        
        self.task_column = ("Title", 'Time', "Status")
        self.task_list = ttk.Treeview(self.right, columns=self.task_column, show="headings", height=6)
        for c in self.task_column: self.task_list.heading(c, text=c); self.task_list.column(c, width=250 if c=="Title" else 150, stretch=False)

        self.session_column = ("Title", 'Starting time', "Ending time", "Status")
        self.session_list = ttk.Treeview(self.right, columns=self.session_column, show="headings", height=6)
        for c in self.session_column: self.session_list.heading(c, text=c); self.session_list.column(c, width=250 if c=="Title" else 100, stretch=False)

        self.window_column = ("Title", 'Starting time', "Ending time")
        self.window_list = ttk.Treeview(self.right, columns=self.window_column, show="headings", height=6)
        for c in self.window_column: self.window_list.heading(c, text=c); self.window_list.column(c, width=250 if c=="Title" else 150, stretch=False)

        ttk.Label(self.right, text="Events for the day").pack(pady=10)
        self.event_list.pack()
        ttk.Label(self.right, text="Tasks for the day").pack(pady=10)
        self.task_list.pack()
        ttk.Label(self.right, text="Work sessions for the day").pack(pady=10)
        self.session_list.pack()
        ttk.Label(self.right, text="Daily unavailable windows").pack(pady=10)
        self.window_list.pack()

        self.date_selected()

    def date_selected(self, event=None):
        selected = self.cal.selection_get()
        tasks, work_seshs, events, self.all_items = self.get_all_information()
        self.all_items.sort(key=lambda item: item["date"])

        for item in self.event_list.get_children(): self.event_list.delete(item)
        for item in self.task_list.get_children(): self.task_list.delete(item)
        for item in self.session_list.get_children(): self.session_list.delete(item)
        for item in self.window_list.get_children(): self.window_list.delete(item)
        for item in self.all_list.get_children(): self.all_list.delete(item)

        for event in events:
            if event["whole_day"] == 0:
                if event["recurrence"] == None:
                    if event["date"] == selected:
                        self.event_list.insert("", "end", iid=event["event_id"], values=(event["title"], event["starting_datetime"], event["ending_datetime"])) 
                else:
                    days = event["recurrence"].split(',')
                    if (selected.strftime('%A')[:3] in days) and selected >= event["date"]:
                        self.event_list.insert("", "end", iid=event["event_id"], values=(event["title"], event["starting_datetime"], event["ending_datetime"])) 

            else:
                if event["starting_datetime"] <= selected and event["ending_datetime"] >= selected:
                    self.event_list.insert("", "end", iid=event["event_id"], values=(event["title"], event["starting_datetime"], event["ending_datetime"])) 

        for task in tasks:
            if task["date"] == selected: 
                self.task_list.insert("", "end", iid=task["task_id"], values=(task["title"], task["due_time"], task["status"]))         

        for sesh in work_seshs:
            if sesh["date"] == selected:
                # "Task name": row["title"], "date": start_dt.date(), "Start time": start_dt.time(), "End time": end_dt.time(), "status": row["status_now"]
                self.session_list.insert("", "end", iid=sesh["session_id"], values=(sesh["title"], sesh["start_time"], sesh["end_time"], sesh["status"]))  

        conn = get_db()
        windows = conn.execute("SELECT rule_id, title, unavailable_start, unavailable_end FROM unavailable_windows")
        for window in windows:
            self.window_list.insert("", "end", iid=window["rule_id"], values=(window["title"], window["unavailable_start"], window["unavailable_end"]))
        # self.window_list.insert()
        conn.close()

        for c in self.all_column: self.all_list.heading(c, text=c); self.all_list.column(c, width=150 if c=="Title" else 100, stretch=False)
        for ind in self.all_items:
            self.all_list.insert("", "end", values=(ind["title"], ind["type"], ind["date"]))
            
    def get_all_information(self):
        conn = get_db()
        tasks, work_sesh, events, all = [], [], [], []
        for row in conn.execute("SELECT task_id, title, due_time, status_now FROM tasks"):
            dt = datetime.fromisoformat(row["due_time"])
            tasks.append({"task_id": row["task_id"], "title": row["title"], "date": dt.date(), "due_time": dt.time(), "status": row["status_now"]})
            all.append({"type": "Task deadline", "title": row["title"], "date": dt.date()})
        for row in conn.execute("SELECT session_id, task_id, start_time, end_time, status_now FROM work_sessions"):
            start_dt = datetime.fromisoformat(row["start_time"])
            end_dt = datetime.fromisoformat(row["end_time"])
            title = conn.execute("SELECT title FROM tasks WHERE task_id = ?", (row["task_id"],)).fetchone()
            work_sesh.append({"session_id": row["session_id"], "title": title["title"], "date": start_dt.date(), "start_time": start_dt.time(), "end_time": end_dt.time(), "status": row["status_now"]})
            all.append({"type": "Work Session", "title": title["title"], "date": start_dt.date()})
        for row in conn.execute("SELECT event_id, title, starting_datetime, ending_datetime, whole_day, recurrence FROM events"):
            dt_start = datetime.fromisoformat(row["starting_datetime"])
            dt_end = datetime.fromisoformat(row["ending_datetime"])
            curr = dt_start
            while True:
                all.append({"type": "Event", "title": row["title"], "date": curr.date()})
                curr += timedelta(days=1)
                if curr.date() > dt_end.date():
                    break

            if row["whole_day"] == 0:
                events.append({"event_id": row["event_id"], "recurrence": row["recurrence"], "whole_day": row["whole_day"], "title": row["title"], "date": dt_start.date(), "starting_datetime": dt_start.time(), "ending_datetime": dt_end.time()})
            else:
                events.append({"event_id": row["event_id"], "whole_day": row["whole_day"], "title": row["title"], "date": dt_start.date(), "starting_datetime": dt_start.date(), "ending_datetime": dt_end.date()})                  
        # print(tasks, work_sesh, events)
        return tasks, work_sesh, events, all

    def accept_selected(self):
        selected = self.session_list.selection()
        # print(selected)
        if not selected:
            messagebox.showinfo("Nothing selected", "Click a work session first.")
            return
        session_id = selected[0]

        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE work_sessions SET status_now = 'accepted' WHERE session_id = ?", (session_id,))
        ws = conn.execute("SELECT task_id, start_time, end_time FROM work_sessions WHERE session_id = ?", (session_id,)).fetchone()
        task_id, start, end = ws[0], ws[1], ws[2]
        start, end = datetime.fromisoformat(start), datetime.fromisoformat(end)
        scheduled_minutes = conn.execute("SELECT scheduled_minute FROM tasks WHERE task_id = ?", (task_id,)).fetchone()[0]
        time = int((end - start).total_seconds()) // 60
        conn.execute(f"UPDATE tasks SET scheduled_minute = ? WHERE task_id = ?", (scheduled_minutes - time, task_id,))
        conn.commit()
        conn.close()
        self.date_selected()    

    def complete_task(self):
        selected = self.task_list.selection()
        if not selected:
            messagebox.showinfo("Nothing selected", "Click on a task first.")
            return

        status = self.task_list.item(selected[0], "values")[2]

        if status != "active":
            messagebox.showinfo("Error", "Click an active task first.")
            return 

        task_id = selected[0]
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE tasks SET status_now = 'completed' WHERE task_id = ?", (task_id,))
        conn.execute("DELETE work_sessions WHERE task_id = ?", (task_id,))
        conn.commit()
        conn.close()
        self.date_selected()  

    def delete_item(self):
        task_selected = self.task_list.selection()
        session_selected = self.session_list.selection()
        event_selected = self.event_list.selection()

        if not task_selected and not session_selected and not event_selected:
            messagebox.showinfo("Nothing selected", "Click on a task / session / event first.")
            return            

        conn = sqlite3.connect(DB_PATH)

        if task_selected:
            conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_selected[0],))
            conn.execute("DELETE FROM work_sessions WHERE task_id = ?", (task_selected[0],))
        elif session_selected:
            conn.execute("DELETE FROM work_sessions WHERE session_id = ?", (session_selected[0],))   
        elif event_selected:
            conn.execute("DELETE FROM events WHERE event_id = ?", (event_selected[0],))   

        conn.commit()
        conn.close()
        self.date_selected()  

    def generate_work(self):
        tasks = genetic2.load_flexible_tasks()
        if not tasks:
            messagebox.showinfo("Nothing to schedule", "No active tasks right now.")
            return
        genetic = genetic2.genetic_algor(30, 60, 0.1)

        conn = get_db()
        conn.execute("DELETE FROM work_sessions WHERE status_now = 'suggested'")
        for sesh in genetic:
            conn.execute("INSERT INTO work_sessions (task_id, start_time, end_time, status_now) VALUES" \
            "(?, ?, ?, ?)", 
            (sesh[0], sesh[1], sesh[2], sesh[3]))
        conn.commit()
        conn.close()
        self.date_selected()

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
        self.date_selected()

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
        self.date_selected()     

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
        self.date_selected()    

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
        self.date_selected() 

           
root = tk.Tk()
calendar = SmartCalendarApp(root)
style = ttk.Style()
style.theme_use("clam")
root.mainloop()