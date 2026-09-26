"""
scheduler.py
------------
Core scheduling logic.

Approach: simple backtracking (constraint satisfaction).
We build a list of "tasks" — one per (section, subject) that needs to be
scheduled — then try to assign each task a (teacher, room, slot) combo
that doesn't conflict with anything already placed. If a choice leads to
a dead end later, we backtrack and try a different combo.

This is intentionally simple. It is NOT optimized and does not do
anything clever like ordering heuristics — that's a later milestone.
The goal right now is just: produce a VALID timetable, or clearly report
that one isn't possible with the given data.
"""

from data import SLOTS, ROOMS, TEACHERS, TEACHER_AVAILABILITY, SECTIONS, SECTION_REQUIREMENTS


class Assignment:
    """One scheduled class: a subject taught to a section by a teacher, in a room, at a slot."""

    def __init__(self, section, subject, teacher, room, slot):
        self.section = section
        self.subject = subject
        self.teacher = teacher
        self.room = room
        self.slot = slot

    def __repr__(self):
        return (f"[{self.slot}] {self.section}: {self.subject} "
                f"with {self.teacher} in {self.room}")


class Scheduler:
    def __init__(self):
        # Build the flat list of tasks that must be scheduled.
        self.tasks = []
        for section, subjects in SECTION_REQUIREMENTS.items():
            for subject in subjects:
                self.tasks.append((section, subject))

        # Conflict-tracking sets: what's already busy at a given slot.
        self.teacher_busy = set()   # (teacher, slot)
        self.room_busy = set()      # (room, slot)
        self.section_busy = set()   # (section, slot)

        self.solution = []          # list of Assignment objects, filled in by solve()

    def qualified_teachers(self, subject):
        """Teachers who can teach this subject."""
        return [t for t, subs in TEACHERS.items() if subject in subs]

    def suitable_rooms(self, section):
        """Rooms big enough to hold this section."""
        section_size = SECTIONS[section]
        return [r for r, cap in ROOMS.items() if cap >= section_size]

    def is_valid(self, section, teacher, room, slot):
        """Check all three hard constraints for placing a class at this slot."""
        if (teacher, slot) in self.teacher_busy:
            return False
        if (room, slot) in self.room_busy:
            return False
        if (section, slot) in self.section_busy:
            return False
        if slot not in TEACHER_AVAILABILITY.get(teacher, []):
            return False
        return True

    def place(self, section, subject, teacher, room, slot):
        self.teacher_busy.add((teacher, slot))
        self.room_busy.add((room, slot))
        self.section_busy.add((section, slot))
        self.solution.append(Assignment(section, subject, teacher, room, slot))

    def remove(self, section, teacher, room, slot):
        self.teacher_busy.discard((teacher, slot))
        self.room_busy.discard((room, slot))
        self.section_busy.discard((section, slot))
        self.solution.pop()

    def solve(self, task_index=0):
        """Recursive backtracking. Returns True if a full valid schedule was found."""
        if task_index == len(self.tasks):
            return True  # every task placed -> success

        section, subject = self.tasks[task_index]
        candidate_teachers = self.qualified_teachers(subject)
        candidate_rooms = self.suitable_rooms(section)

        for teacher in candidate_teachers:
            for room in candidate_rooms:
                for slot in SLOTS:
                    if self.is_valid(section, teacher, room, slot):
                        self.place(section, subject, teacher, room, slot)
                        if self.solve(task_index + 1):
                            return True
                        self.remove(section, teacher, room, slot)  # backtrack

        return False  # no combo worked for this task -> dead end, backtrack further

    def generate(self):
        """Public entry point. Returns (success: bool, solution: list[Assignment])."""
        success = self.solve()
        return success, self.solution
