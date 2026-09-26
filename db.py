"""
db.py
-----
SQLite storage for the user's OWN editable timetable entries.

This is deliberately separate from scheduler.py / data.py, which power the
optional "auto-generate a sample timetable" feature. Here, subjects are
NOT mandatory or predefined — the user adds whatever classes they actually
have, at whatever days/times they choose, and it's saved so it survives a
browser refresh or server restart.

Table: entries
  id          - auto-increment primary key
  subject     - free text, user-chosen (e.g. "Data Structures")
  teacher     - free text, optional
  day         - one of Monday..Sunday
  start_time  - "HH:MM" 24-hour
  end_time    - "HH:MM" 24-hour
  notes       - free text, optional (e.g. "Room 204", "Bring calculator")
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "timetable.db"

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            teacher TEXT,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def _row_to_dict(row):
    return {
        "id": row["id"],
        "subject": row["subject"],
        "teacher": row["teacher"] or "",
        "day": row["day"],
        "start_time": row["start_time"],
        "end_time": row["end_time"],
        "notes": row["notes"] or "",
    }


def list_entries():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM entries").fetchall()
    conn.close()
    entries = [_row_to_dict(r) for r in rows]
    # Sort by day-of-week order, then start time — nicer than DB insertion order.
    entries.sort(key=lambda e: (DAY_ORDER.index(e["day"]), e["start_time"]))
    return entries


def get_entry(entry_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def find_conflicts(day, start_time, end_time, exclude_id=None):
    """
    Two entries conflict if they're on the same day and their time ranges
    overlap: new.start < existing.end AND new.end > existing.start.
    Returns a list of conflicting entries (as dicts).
    """
    conn = get_connection()
    query = """
        SELECT * FROM entries
        WHERE day = ?
          AND start_time < ?
          AND end_time > ?
    """
    params = [day, end_time, start_time]
    if exclude_id is not None:
        query += " AND id != ?"
        params.append(exclude_id)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def add_entry(subject, teacher, day, start_time, end_time, notes):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO entries (subject, teacher, day, start_time, end_time, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (subject, teacher, day, start_time, end_time, notes),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return get_entry(new_id)


def update_entry(entry_id, subject, teacher, day, start_time, end_time, notes):
    conn = get_connection()
    conn.execute(
        "UPDATE entries SET subject = ?, teacher = ?, day = ?, start_time = ?, "
        "end_time = ?, notes = ? WHERE id = ?",
        (subject, teacher, day, start_time, end_time, notes, entry_id),
    )
    conn.commit()
    conn.close()
    return get_entry(entry_id)


def delete_entry(entry_id):
    conn = get_connection()
    conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
