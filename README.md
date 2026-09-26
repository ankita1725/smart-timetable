# My Timetable

**Milestone 2: editable personal timetable, backed by SQLite, with the
original auto-generator kept as an optional secondary feature.**

## Project structure

```text
smart-timetable/
│
├── app.py              ← Flask server. Two independent feature sets (see below).
├── db.py               ← SQLite layer for the user's editable entries
├── timetable.db         ← created automatically on first run (not committed)
│
├── main.py             ← old console-only entry point for the sample generator
├── data.py             ← sample data for the OPTIONAL auto-generator only
├── scheduler.py         ← the backtracking scheduling engine (untouched)
│
├── templates/
│   └── index.html      ← page markup: Add/Edit form, your classes table,
│                          collapsed "auto-generate" panel
├── static/
│   ├── style.css
│   └── script.js
├── requirements.txt
└── README.md
```

## Running it

```bash
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**.

## What changed from Milestone 1

The project now has two, separate feature areas:

### 1. Your own editable timetable (new, primary)

- No fixed or mandatory subjects — you type in whatever class you actually have.
- Add a class: subject, teacher (optional), day, start time, end time, notes (optional).
- Edit or delete any class from the table.
- **Conflict checking**: if a new or edited class overlaps another one on the
  same day, it's rejected with a message naming what it clashes with.
- **Persists in SQLite** (`timetable.db`) — refreshing the browser or
  restarting the server does not lose your data.

API:
```text
GET    /api/entries          list your classes
POST   /api/entries          add a class (conflict-checked)
PUT    /api/entries/<id>     edit a class (conflict-checked)
DELETE /api/entries/<id>     remove a class
```

### 2. Auto-generate a sample timetable (old feature, now optional)

Everything from Milestone 1 still works exactly as before — `scheduler.py`
and `data.py` were **not touched**. It's now tucked under a collapsed
"Auto-generate a sample timetable" panel on the page, since it's a demo/
admin tool (fixed sample teachers/rooms/sections) rather than something
tied to your own classes.

API: `GET /api/generate`, `GET /api/meta` (unchanged, just renamed from
`/api/timetable` to make the split clear).

## Data model (SQLite)

One table, `entries`:

| column      | meaning                              |
|-------------|---------------------------------------|
| id          | auto-increment id                     |
| subject     | free text, whatever you call it       |
| teacher     | free text, optional                   |
| day         | Monday..Sunday                        |
| start_time  | "HH:MM", 24-hour                      |
| end_time    | "HH:MM", 24-hour                      |
| notes       | free text, optional (room, reminders) |

Conflict rule: two entries conflict if they're on the same `day` and their
time ranges overlap (`new.start < existing.end AND new.end > existing.start`).
This is a single shared timetable for now — no per-user separation yet
(that's the login step below).

## Roadmap (in order)

1. ~~Make the timetable editable~~ ✅
2. ~~Remove mandatory/fixed subjects~~ ✅
3. ~~SQLite database~~ ✅
4. **Login / per-user timetables** — right now all entries are shared;
   next step is tagging entries with a user id so each student/user has
   their own timetable.
5. **Google Calendar integration** — once entries belong to a user, push
   each entry as a recurring Calendar event (needs Google OAuth, so it
   depends on step 4 being done first) so reminders show up automatically.
6. **UI polish + deployment.**

## Trying the old sample generator's data

Edit `data.py` (teachers, rooms, sections, availability, requirements) —
this only affects the optional panel, not your own saved classes. Rerun
via the "Run sample generator" button, or `python main.py` for
console-only output.
