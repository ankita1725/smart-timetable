"""
main.py
-------
Run this to generate and print a timetable:

    python main.py
"""

from scheduler import Scheduler
from data import SECTIONS, SLOTS


def print_timetable(solution):
    """Pretty-print the schedule as one grid per section: rows=slots."""
    for section in SECTIONS:
        print(f"\n=== Timetable: Section {section} ===")
        print(f"{'Slot':<8} | {'Subject':<18} | {'Teacher':<12} | Room")
        print("-" * 55)
        # Pull out and sort this section's classes by slot order
        section_classes = [a for a in solution if a.section == section]
        section_classes.sort(key=lambda a: SLOTS.index(a.slot))
        for a in section_classes:
            print(f"{a.slot:<8} | {a.subject:<18} | {a.teacher:<12} | {a.room}")


def main():
    scheduler = Scheduler()
    success, solution = scheduler.generate()

    if not success:
        print("Could not generate a valid timetable with the given data.")
        print("Try loosening constraints (add teachers, rooms, or available slots).")
        return

    print("Timetable generated successfully with no conflicts.\n")
    print_timetable(solution)


if __name__ == "__main__":
    main()
