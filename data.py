"""
data.py
-------
All the raw input data for the timetable scheduler lives here.
Keeping it separate from scheduler.py means you can swap this out
for a database or a form/UI later without touching the scheduling logic.
"""

# ---- Time slots available in a day ----
SLOTS = ["9-10", "10-11", "11-12", "12-1", "2-3"]

# ---- Rooms and their seating capacity ----
ROOMS = {
    "R1": 40,
    "R2": 30,
    "R3": 60,
}

# ---- Teachers and which subjects they are qualified to teach ----
TEACHERS = {
    "Mr. Sharma": ["Math", "Physics"],
    "Ms. Verma":  ["Physics", "Chemistry"],
    "Mr. Iyer":   ["Math", "Computer Science"],
    "Ms. Rao":    ["Chemistry", "Biology"],
}

# ---- Teacher availability: slots each teacher is free to teach ----
# (If a teacher isn't listed for a slot, they're considered unavailable then.)
TEACHER_AVAILABILITY = {
    "Mr. Sharma": ["9-10", "10-11", "11-12", "2-3"],
    "Ms. Verma":  ["9-10", "10-11", "12-1", "2-3"],
    "Mr. Iyer":   ["10-11", "11-12", "12-1", "2-3"],
    "Ms. Rao":    ["9-10", "11-12", "12-1", "2-3"],
}

# ---- Student sections and how many students are in each ----
SECTIONS = {
    "10-A": 35,
    "10-B": 28,
    "11-A": 45,
}

# ---- Required subjects (and how many periods/week) for each section ----
# This is what the scheduler must actually place on the timetable.
SECTION_REQUIREMENTS = {
    "10-A": ["Math", "Physics", "Chemistry"],
    "10-B": ["Math", "Computer Science", "Biology"],
    "11-A": ["Physics", "Chemistry", "Math"],
}
