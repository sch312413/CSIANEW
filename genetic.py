import random 
import sqlite3
from datetime import datetime, timedelta
# ---------------------------------------------------------------------
# getting the tasks and contraints 
# ---------------------------------------------------------------------

def load_flexible_tasks():
    # Return the tasks that still need scheduling
    conn = sqlite3.connect("database.db")
    need_schedule_tasks = conn.execute(
        """SELECT task_id, title, due_time, total_minutes, scheduled_minute, status_now 
        FROM tasks WHERE status_now = "active" ORDER BY due_time"""
    ).fetchall()
    conn.close()
    return need_schedule_tasks

def event_blocks():
    # occupied time and no moving - fixed events and locked sessh
    conn = sqlite3.connect("database.db")
    fixed_events = conn.execute(
        """SELECT title, event_type, whole_day, recurrence, starting_datetime, ending_datetime
        FROM events"""
    ).fetchall()
    conn.close()
    return fixed_events

def accepted_blocks():
    conn = sqlite3.connect("database.db") 
    accepted_working = conn.execute(
            """SELECT task_id, start_time, end_time, status_now
            FROM work_sessions WHERE status_now = "accepted"
            """).fetchall()
    conn.close()
    return accepted_working

def load_constraints_tasks():
    conn = sqlite3.connect("database.db")
    user_pref = conn.execute(
            """SELECT settings_id, max_working, min_break, max_session_minutes
            FROM settings
            """).fetchall()
    conn.close()
    return user_pref

# for convenience when needed 
def combine_date_time(date_str, time_str):
    return datetime.combine(datetime.strptime(date_str, "%Y-%m-%d").date(), datetime.strptime(time_str, "%H:%M").time())

# iterates thru all daily blocks to make sure nothing goes there 
def time_phase(start_time, end_time):
    sesh = []
    start_time = datetime.strptime(start_time, "%H:%M").time()
    end_time = datetime.strptime(end_time, "%H:%M").time()

    curr = datetime.combine(datetime(2000, 1, 1), start_time)
    
    while curr != end_time:
        sesh.append(curr.time())
        curr += timedelta(minutes=5)
        
    return sesh

def day_unavailable():
    whole_day = time_phase("00:00", "23:59")
    conn = sqlite3.connect("database.db")
    unavailable_slots = conn.execute(
            """SELECT title, unavailable_start, unavailable_end
            FROM unavailable_windows
            """
        ).fetchall()
    conn.close()

    for slot in unavailable_slots:
        begin_time, end_time = slot[1], slot[2]
        if begin_time < end_time:
            unavailable_day = time_phase("00:00", str(end_time))[:-1]
            unavailable_night = time_phase(str(begin_time), "23:59")[1:]
            # print(unavailable_day)
            whole_day = [slot for slot in whole_day if slot not in unavailable_day]
            whole_day = [slot for slot in whole_day if slot not in unavailable_night] 
        else:
            whole_day = [slot for slot in whole_day if slot not in time_phase(str(begin_time), str(end_time))[1:-1]]
    return sorted(whole_day)              
DAY_AVAIL_SLOTS = day_unavailable()

# iterating thru all of the times that are 
def fixed_before_time(window_start, window_end): # both should be datetime already 
    concrete_blocks = []
    # events 
    fixed_events = event_blocks()
    for event in fixed_events:
        whole_day, recurrence = event[2], event[3]
        starting_datetime, ending_datetime = datetime.fromisoformat(event[4]), datetime.fromisoformat(event[5])

        if whole_day or recurrence == None: concrete_blocks.append((starting_datetime, ending_datetime))
        else:
            repeated_days = recurrence.split(',')
            cursor = window_start
            while cursor <= window_end:
                if cursor.strftime("%a") in repeated_days:
                    concrete_blocks.append((datetime.combine(cursor.date(), starting_datetime.time()), datetime.combine(cursor.date(), ending_datetime.time())))
                cursor += timedelta(days=1)
    # accepted blocks 
    working_alr = accepted_blocks()
    for work_sesh in working_alr:
        work_start, work_end = datetime.fromisoformat(work_sesh[1]), datetime.fromisoformat(work_sesh[2])
        concrete_blocks.append((work_start, work_end))

    return concrete_blocks
    
# gene generation 
def random_gene_generation(task_id, session_length, dates_before_due, real_due): # i want to input the datetime type 
    while True:
        random_date = random.choice(dates_before_due)
        
        random_time = random.choice(DAY_AVAIL_SLOTS)
        start = datetime.combine(random_date, random_time)
        # start = combine_date_time(datetime.strftime(random_date, "%Y-%m-%d"), random_time)
        end = start + timedelta(minutes=session_length)
        if end <= real_due and end in DAY_AVAIL_SLOTS:
            return (task_id, start.strftime('%Y-%m-%dT%H:%M'), end.strftime('%Y-%m-%dT%H:%M'), 'suggested')

def generating_minutes(working_hours, max_working):
    sessions = []
    under = []
    if working_hours <= 5:
        sessions.append(5)
        return sessions
    while working_hours > 0:
        if working_hours >= max_working:
            session_length = random.randrange(5, max_working, 5)
            sessions.append(session_length)
            if session_length < (max_working - 5):
                under.append(len(sessions) - 1)
            working_hours -= session_length
        elif working_hours <= 5:
            if len(under) >= 1:
                n = under[random.randint(0, len(under)-1)]
                sessions[n] += working_hours
                working_hours = 0
            else:
                sessions.append(working_hours)
                working_hours = 0
        else:
            session_length = random.randrange(5, working_hours, 5)
            sessions.append(session_length)
            working_hours -= session_length
        # print(session_length, working_hours, max_working)
    return sessions

def random_gene_everything(task, preferences):
    '''all random sessions - considers the daily unavailables'''
    # task dict
    task_id, task_name = task[0], task[1]
    task_due = datetime.fromisoformat(task[2])
    needed_time, scheduled_time = task[3], task[4]
    need_to_schedule = needed_time - scheduled_time
    session_limit = preferences[3]

    # dates before due
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
 
    dates_before_due = []
    one_day = timedelta(days=1)
    cursor = today
    while cursor <= task_due:
        dates_before_due.append(cursor)
        cursor += one_day

    # random session generation
    gene_list = []
    session_list = generating_minutes(need_to_schedule, session_limit)
    for one_session in session_list:
        gene_list.append(random_gene_generation(task_id, one_session, dates_before_due, task_due))
    return gene_list

def build_random_individual(flexible_tasks, preferences):
    individual = []
    for task in flexible_tasks:
        individual.extend(random_gene_everything(task, preferences))
    return individual

# GA fahh 
def overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end

def fitness(individual, fixed_blocks, settings, tasks_by_id):
    score = 0 
    per_day = {}
    max_working = settings[1]
    min_break = settings[2]

    for gene in individual:
        start, end = datetime.fromisoformat(gene[1]), datetime.fromisoformat(gene[2])
        if start.date() not in per_day: 
            per_day[start.date()] = [[start, end]]
        else:
            per_day[start.date()].append([start, end])

        for block_start, block_end in fixed_blocks:
            if overlaps(start, end, block_start, block_end):
                score -= 30 

    for i in range(len(individual)):
        for j in range(i+1, len(individual)):
            gene1, gene2 = individual[i], individual[j]
            gene1_start, gene1_end = datetime.fromisoformat(gene1[1]), datetime.fromisoformat(gene1[2])
            gene2_start, gene2_end = datetime.fromisoformat(gene2[1]), datetime.fromisoformat(gene2[2])
            if overlaps(gene1_start, gene1_end, gene2_start, gene2_end):
                score -= 30 

    for date in per_day.values():
        working_time = 0 
        for i in range(len(date)):
            time1_start, time1_end = date[i][0], date[i][1]
            working_time += int((time1_end - time1_start).total_seconds()//60)
            for j in range(i+1, len(date)):
                time2_start, time2_end = date[j][0], date[j][1]
                difference1 = int((time1_start - time2_end).total_seconds()//60)
                difference2 = int((time2_start - time1_end).total_seconds()//60)
                if difference1 < min_break and difference1 > 0:
                    score -= (difference1 - min_break)
                elif difference2 < min_break and difference2 > 0:
                    score -= (difference2 - min_break)

        if working_time > max_working:
            score -= (working_time - max_working)
    return score 

def select_parent(population_with_fitness):
    min_fitness = min(f for _, f in population_with_fitness)
    shift = abs(min_fitness) + 1
    total = sum(f + shift for _, f in population_with_fitness)

    pick = random.uniform(0, total)
    running_total = 0
    for individual, f in population_with_fitness:
        running_total += f + shift
        if running_total >= pick:
            return individual
    return population_with_fitness[-1][0]

def crossover(parent_a, parent_b, task_ids):
    child = []
    for task_id in task_ids:
        choice = random.randint(0, 1)
        if choice == 0: 
            child.extend([gene for gene in parent_a if gene[0] == task_id])
        else:
            child.extend([gene for gene in parent_b if gene[0] == task_id])
    return child 

def mutate(today, individual, mutation_rate, tasks_by_id, settings, available_slots):
    mutated = []
    for gene in individual:
        if random.random() < mutation_rate:
            task = tasks_by_id[gene[0]]
            due_datetime = datetime.fromisoformat(task[2])
            gene_start, gene_end = datetime.fromisoformat(gene[1]), datetime.fromisoformat(gene[2])
            length = int((gene_end - gene_start).total_seconds() // 60)

            dates_before_due = []
            cursor = today 
            while cursor <= due_datetime:
                dates_before_due.append(cursor)
                cursor += timedelta(days=1)

            mutated.append(random_gene_generation(gene[0], length, dates_before_due, due_datetime))
        else:
            mutated.append(gene)
    return mutated

def genetic_algor(population_size, generations, mutation_rate):
    tasks = load_flexible_tasks()
    tasks_by_id = {t[0]: t for t in tasks}
    task_ids = [t[0] for t in tasks]
    settings = load_constraints_tasks()[0]
    
    furthest_due = max((datetime.fromisoformat(t[2]) for t in tasks))

    now = datetime.now()
    CEIL = now + (timedelta(minutes=15) - timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)) % timedelta(minutes=15)
    fixed_blocks = fixed_before_time(CEIL, furthest_due)

    population = [build_random_individual(tasks, settings) for _ in range(population_size)]
    best_individual = None

    for generation in range(generations):
        scored = [(ind, fitness(ind, fixed_blocks, settings, tasks_by_id)) for ind in population]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        best_individual, best_fitness = scored[0]

        next_population = [best_individual]
        while len(next_population) < population_size:
            parent_a = select_parent(scored)
            parent_b = select_parent(scored)
            child = mutate(CEIL, crossover(parent_a, parent_b, task_ids), mutation_rate, tasks_by_id, settings, DAY_AVAIL_SLOTS)
            next_population.append(child)
        population = next_population

    return best_individual

if __name__ == "__main__":
    best = genetic_algor(30, 60, 0.1)
    print(best)
