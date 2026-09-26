"""
app.py
------
Flask layer with two independent features:

1. YOUR OWN EDITABLE TIMETABLE (new, primary feature)
   Backed by db.py / SQLite. No fixed/mandatory subjects — you add
   whatever classes you actually have. Persists across restarts.
     GET    /api/entries
     POST   /api/entries
     PUT    /api/entries/<id>
     DELETE /api/entries/<id>

2. AUTO-GENERATE A SAMPLE TIMETABLE (old feature, kept, optional)
   Backed by scheduler.py / data.py, untouched. Useful as a demo or for
   an admin generating a starting timetable for a whole class/section.
     GET /api/generate
     GET /api/meta

Run:
    python app.py
Then open:
    http://127.0.0.1:5000
"""

import time
from flask import Flask, jsonify, render_template, request

import db
from scheduler import Scheduler
from data import SLOTS, SECTIONS, ROOMS, TEACHERS, SECTION_REQUIREMENTS

app = Flask(__name__)
db.init_db()

VALID_DAYS = set(db.DAY_ORDER)


@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------
# 1. Editable timetable entries (SQLite-backed)
# ---------------------------------------------------------------------

def _normalize_time(value):
    """
    Parse "H:MM" or "HH:MM" (24-hour) into a zero-padded "HH:MM" string, so
    later string comparisons (both in Python and in SQL) sort correctly.
    Returns None if the value isn't a valid time.
    """
    value = (value or "").strip()
    parts = value.split(":")
    if len(parts) != 2:
        return None
    try:
        hour, minute = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return f"{hour:02d}:{minute:02d}"


def _parse_entry_payload(data):
    """
    Validates and normalizes an entry payload.
    Returns (clean_dict, None) on success, or (None, error_message) on failure.
    """
    subject = (data.get("subject") or "").strip()
    teacher = (data.get("teacher") or "").strip()
    day = (data.get("day") or "").strip()
    notes = (data.get("notes") or "").strip()
    start_time = _normalize_time(data.get("start_time"))
    end_time = _normalize_time(data.get("end_time"))

    if not subject:
        return None, "Subject name is required."
    if day not in VALID_DAYS:
        return None, f"Day must be one of: {', '.join(db.DAY_ORDER)}."
    if start_time is None or end_time is None:
        return None, "Start time and end time must be valid times (HH:MM)."
    if start_time >= end_time:
        return None, "End time must be after start time."

    return {
        "subject": subject,
        "teacher": teacher,
        "day": day,
        "start_time": start_time,
        "end_time": end_time,
        "notes": notes,
    }, None


@app.route("/api/entries", methods=["GET"])
def get_entries():
    return jsonify({"entries": db.list_entries()})


@app.route("/api/entries", methods=["POST"])
def create_entry():
    data = request.get_json(force=True, silent=True) or {}
    clean, error = _parse_entry_payload(data)
    if error:
        return jsonify({"error": error}), 400

    conflicts = db.find_conflicts(clean["day"], clean["start_time"], clean["end_time"])
    if conflicts:
        return jsonify({
            "error": "This overlaps with a class you already have.",
            "conflicts": conflicts,
        }), 409

    entry = db.add_entry(**clean)
    return jsonify({"entry": entry}), 201


@app.route("/api/entries/<int:entry_id>", methods=["PUT"])
def edit_entry(entry_id):
    if db.get_entry(entry_id) is None:
        return jsonify({"error": "No entry with that id."}), 404

    data = request.get_json(force=True, silent=True) or {}
    clean, error = _parse_entry_payload(data)
    if error:
        return jsonify({"error": error}), 400

    conflicts = db.find_conflicts(clean["day"], clean["start_time"], clean["end_time"], exclude_id=entry_id)
    if conflicts:
        return jsonify({
            "error": "This overlaps with a class you already have.",
            "conflicts": conflicts,
        }), 409

    entry = db.update_entry(entry_id, **clean)
    return jsonify({"entry": entry})


@app.route("/api/entries/<int:entry_id>", methods=["DELETE"])
def remove_entry(entry_id):
    if db.get_entry(entry_id) is None:
        return jsonify({"error": "No entry with that id."}), 404
    db.delete_entry(entry_id)
    return jsonify({"deleted": entry_id})


# ---------------------------------------------------------------------
# 2. Optional: auto-generate a sample timetable (old feature, unchanged)
# ---------------------------------------------------------------------

@app.route("/api/generate")
def api_generate():
    """Run the backtracking scheduler on data.py's sample data."""
    start = time.time()
    scheduler = Scheduler()
    success, solution = scheduler.generate()
    elapsed_ms = round((time.time() - start) * 1000, 1)

    assignments = [
        {
            "section": a.section,
            "subject": a.subject,
            "teacher": a.teacher,
            "room": a.room,
            "slot": a.slot,
        }
        for a in solution
    ]

    total_required = sum(len(subs) for subs in SECTION_REQUIREMENTS.values())

    return jsonify({
        "success": success,
        "generated_in_ms": elapsed_ms,
        "slots": SLOTS,
        "sections": list(SECTIONS.keys()),
        "total_required": total_required,
        "total_placed": len(assignments),
        "assignments": assignments,
    })


@app.route("/api/meta")
def api_meta():
    """Reference data behind the sample generator (read-only)."""
    return jsonify({
        "rooms": ROOMS,
        "teachers": TEACHERS,
        "sections": SECTIONS,
        "requirements": SECTION_REQUIREMENTS,
    })


if __name__ == "__main__":
    app.run(debug=True)
