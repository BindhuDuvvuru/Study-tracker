# ============================================================
# Student Study Tracker - Main Application File
# ============================================================
# This file sets up the Flask web server and handles all routes
# (pages) and database operations.

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
import math

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = "studytracker_secret_key_2024"  # Needed for flash messages

# Path to our SQLite database file
DATABASE = os.path.join(os.path.dirname(__file__), "database.db")


# ============================================================
# DATABASE HELPER FUNCTIONS
# ============================================================

def get_db():
    """Open a connection to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_db():
    """Create all necessary database tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()

    # Subjects table — stores each subject the student is studying
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            difficulty  TEXT NOT NULL,      -- 'easy', 'medium', 'hard'
            exam_date   TEXT NOT NULL,      -- stored as YYYY-MM-DD
            progress    INTEGER DEFAULT 0,  -- 0 to 100 (percentage)
            notes       TEXT DEFAULT '',    -- optional notes for the subject
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Timetable table — stores auto-generated study slots
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id  INTEGER NOT NULL,
            day_name    TEXT NOT NULL,      -- e.g., 'Monday'
            hours       REAL NOT NULL,      -- hours assigned to that slot
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# HELPER / CALCULATION FUNCTIONS
# ============================================================

def days_until_exam(exam_date_str):
    """Return how many days remain until the given exam date."""
    try:
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        delta = (exam_date - today).days
        return delta
    except Exception:
        return 999  # If date is invalid, treat as far future


def difficulty_weight(difficulty):
    """Convert difficulty label to a numeric weight for scheduling."""
    return {"easy": 1, "medium": 2, "hard": 3}.get(difficulty, 1)


def calculate_priority(subject):
    """
    Calculate a priority score for a subject.
    Lower score = higher priority (should be studied first).
    Formula: days_left / difficulty_weight
    Fewer days + higher difficulty = top priority.
    """
    days_left = days_until_exam(subject["exam_date"])
    if days_left <= 0:
        days_left = 1  # Avoid division by zero; exam is today/past
    weight = difficulty_weight(subject["difficulty"])
    return days_left / weight


def generate_timetable(subjects, hours_per_day):
    """
    Generate a weekly timetable by distributing study hours across
    the 7 days of the week, prioritizing subjects with:
      - Nearest exam dates
      - Higher difficulty levels
    Returns a list of timetable slot dictionaries.
    """
    if not subjects or hours_per_day <= 0:
        return []

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    total_weekly_hours = hours_per_day * 7

    # Sort subjects by priority (lowest score = highest priority)
    sorted_subjects = sorted(subjects, key=lambda s: calculate_priority(s))

    # Assign weights — most priority gets the most hours
    total_weight = sum(difficulty_weight(s["difficulty"]) for s in sorted_subjects)
    slots = []

    # Distribute hours across subjects proportionally by difficulty weight
    remaining_hours = total_weekly_hours
    for i, subject in enumerate(sorted_subjects):
        weight = difficulty_weight(subject["difficulty"])
        subject_hours = round((weight / total_weight) * total_weekly_hours, 1)

        # Spread this subject's hours across multiple days
        hours_left = subject_hours
        day_index = i % 7  # Start on different days to spread the load

        while hours_left > 0 and days:
            daily_slot = min(hours_left, hours_per_day)
            daily_slot = min(daily_slot, 2.5)  # Cap at 2.5 hours per subject/day
            if daily_slot < 0.5:
                break
            slots.append({
                "subject_id": subject["id"],
                "subject_name": subject["name"],
                "day_name": days[day_index % 7],
                "hours": round(daily_slot, 1)
            })
            hours_left = round(hours_left - daily_slot, 1)
            day_index += 1

    return slots


# ============================================================
# ROUTES — PAGES OF THE WEB APP
# ============================================================

@app.route("/")
def dashboard():
    """
    Main dashboard page — shows summary stats and upcoming exams.
    """
    conn = get_db()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY exam_date ASC").fetchall()
    conn.close()

    subjects = [dict(s) for s in subjects]

    # Attach extra info to each subject for the template
    for s in subjects:
        s["days_left"] = days_until_exam(s["exam_date"])
        s["priority"] = round(calculate_priority(s), 2)

    # Dashboard statistics
    total_subjects = len(subjects)
    avg_progress = round(sum(s["progress"] for s in subjects) / total_subjects, 1) if total_subjects else 0
    upcoming = [s for s in subjects if 0 <= s["days_left"] <= 7]
    overdue  = [s for s in subjects if s["days_left"] < 0]

    return render_template(
        "index.html",
        subjects=subjects,
        total_subjects=total_subjects,
        avg_progress=avg_progress,
        upcoming=upcoming,
        overdue=overdue
    )


@app.route("/subjects", methods=["GET", "POST"])
def subjects():
    """
    Subject management page — add, edit, delete subjects and notes.
    """
    conn = get_db()

    if request.method == "POST":
        action = request.form.get("action", "add")

        # ---- ADD a new subject ----
        if action == "add":
            name       = request.form.get("name", "").strip()
            difficulty = request.form.get("difficulty", "medium")
            exam_date  = request.form.get("exam_date", "")
            notes      = request.form.get("notes", "").strip()

            # Basic validation
            if not name:
                flash("Subject name cannot be empty.", "error")
            elif not exam_date:
                flash("Please enter an exam date.", "error")
            else:
                conn.execute(
                    "INSERT INTO subjects (name, difficulty, exam_date, notes) VALUES (?, ?, ?, ?)",
                    (name, difficulty, exam_date, notes)
                )
                conn.commit()
                flash(f'Subject "{name}" added successfully!', "success")

        # ---- UPDATE an existing subject ----
        elif action == "edit":
            subject_id = request.form.get("subject_id")
            name       = request.form.get("name", "").strip()
            difficulty = request.form.get("difficulty", "medium")
            exam_date  = request.form.get("exam_date", "")
            notes      = request.form.get("notes", "").strip()
            progress   = request.form.get("progress", 0)

            if not name or not exam_date:
                flash("Name and exam date are required.", "error")
            else:
                conn.execute(
                    """UPDATE subjects
                       SET name=?, difficulty=?, exam_date=?, notes=?, progress=?
                       WHERE id=?""",
                    (name, difficulty, exam_date, notes, int(progress), subject_id)
                )
                conn.commit()
                flash(f'Subject "{name}" updated!', "success")

        # ---- DELETE a subject ----
        elif action == "delete":
            subject_id = request.form.get("subject_id")
            conn.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
            conn.commit()
            flash("Subject deleted.", "info")

        conn.close()
        return redirect(url_for("subjects"))

    # GET request — just show the subjects list
    all_subjects = conn.execute("SELECT * FROM subjects ORDER BY exam_date ASC").fetchall()
    conn.close()

    all_subjects = [dict(s) for s in all_subjects]
    for s in all_subjects:
        s["days_left"] = days_until_exam(s["exam_date"])

    return render_template("subjects.html", subjects=all_subjects)


@app.route("/timetable", methods=["GET", "POST"])
def timetable():
    """
    Timetable generator page — user enters hours/day and gets a
    smart weekly study schedule.
    """
    conn = get_db()
    generated_slots = []
    hours_input = 0

    if request.method == "POST":
        try:
            hours_input = float(request.form.get("hours_per_day", 0))
            if hours_input <= 0:
                flash("Please enter a positive number of hours.", "error")
            elif hours_input > 16:
                flash("Maximum 16 hours per day allowed.", "error")
            else:
                subjects = conn.execute("SELECT * FROM subjects ORDER BY exam_date ASC").fetchall()
                subjects = [dict(s) for s in subjects]

                if not subjects:
                    flash("Please add subjects first before generating a timetable.", "error")
                else:
                    # Delete any previous timetable
                    conn.execute("DELETE FROM timetable")

                    # Generate new timetable
                    generated_slots = generate_timetable(subjects, hours_input)

                    # Save to database
                    for slot in generated_slots:
                        conn.execute(
                            "INSERT INTO timetable (subject_id, day_name, hours) VALUES (?, ?, ?)",
                            (slot["subject_id"], slot["day_name"], slot["hours"])
                        )
                    conn.commit()
                    flash("Timetable generated successfully!", "success")
        except ValueError:
            flash("Invalid input. Please enter a valid number.", "error")

    # Always fetch the current timetable from DB to display
    rows = conn.execute("""
        SELECT t.id, t.day_name, t.hours, s.name as subject_name, s.difficulty
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        ORDER BY
            CASE t.day_name
                WHEN 'Monday'    THEN 1
                WHEN 'Tuesday'   THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday'  THEN 4
                WHEN 'Friday'    THEN 5
                WHEN 'Saturday'  THEN 6
                WHEN 'Sunday'    THEN 7
            END
    """).fetchall()
    conn.close()

    # Organize by day for the weekly table view
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    timetable_by_day = {day: [] for day in days}
    for row in rows:
        row = dict(row)
        timetable_by_day[row["day_name"]].append(row)

    return render_template(
        "timetable.html",
        timetable_by_day=timetable_by_day,
        days=days,
        hours_input=hours_input
    )


@app.route("/progress", methods=["GET", "POST"])
def progress():
    """
    Progress tracker page — update and view how much of each subject
    has been completed.
    """
    conn = get_db()

    if request.method == "POST":
        subject_id  = request.form.get("subject_id")
        new_progress = request.form.get("progress", 0)
        try:
            new_progress = max(0, min(100, int(new_progress)))  # Clamp 0-100
            conn.execute(
                "UPDATE subjects SET progress=? WHERE id=?",
                (new_progress, subject_id)
            )
            conn.commit()
            flash("Progress updated!", "success")
        except ValueError:
            flash("Invalid progress value.", "error")

        conn.close()
        return redirect(url_for("progress"))

    all_subjects = conn.execute("SELECT * FROM subjects ORDER BY name ASC").fetchall()
    conn.close()
    all_subjects = [dict(s) for s in all_subjects]

    return render_template("progress.html", subjects=all_subjects)


@app.route("/exam-schedule")
def exam_schedule():
    """
    Exam preparation scheduler — shows days left and suggested
    daily study hours for each subject.
    """
    conn = get_db()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY exam_date ASC").fetchall()
    conn.close()

    subjects = [dict(s) for s in subjects]
    schedule = []

    for s in subjects:
        days_left = days_until_exam(s["exam_date"])
        weight = difficulty_weight(s["difficulty"])
        remaining = 100 - s["progress"]

        # Suggest hours per day: more hours for harder/closer subjects
        if days_left > 0:
            suggested_daily = round((weight * remaining / 100) * 2 / max(days_left, 1), 1)
            suggested_daily = max(0.5, min(suggested_daily, 4.0))  # Between 30 min and 4 hrs
        else:
            suggested_daily = 0

        schedule.append({
            **s,
            "days_left": days_left,
            "suggested_daily": suggested_daily,
            "urgency": "high" if days_left <= 3 else ("medium" if days_left <= 7 else "low")
        })

    return render_template("exam_schedule.html", schedule=schedule)


# ============================================================
# RUN THE APP
# ============================================================

if __name__ == "__main__":
    init_db()           # Make sure tables exist before starting
    print("✅ Study Tracker is running at http://127.0.0.1:5000")
    app.run(debug=True)  # debug=True shows errors in the browser during development
