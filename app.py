from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "devopsx.db")

app = Flask(__name__)
app.secret_key = os.environ.get("DEVOPSX_SECRET", "change-this-in-production")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                repository_url TEXT NOT NULL,
                environment TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM deployments").fetchone()[0]
        if count == 0:
            demo = [
                ("Campus Portal", "https://github.com/example/campus-portal", "Staging", "Success", "Demo deployment completed"),
                ("Library API", "https://github.com/example/library-api", "Production", "Failed", "Demo: missing environment variable"),
                ("Student Dashboard", "https://github.com/example/student-dashboard", "Development", "Running", "Demo deployment in progress"),
            ]
            conn.executemany(
                "INSERT INTO deployments (project_name, repository_url, environment, status, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                [(p, r, e, s, n, datetime.now().strftime("%Y-%m-%d %H:%M")) for p, r, e, s, n in demo]
            )

@app.route("/")
def dashboard():
    with get_db() as conn:
        deployments = conn.execute("SELECT * FROM deployments ORDER BY id DESC").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM deployments").fetchone()[0]
        success = conn.execute("SELECT COUNT(*) FROM deployments WHERE status='Success'").fetchone()[0]
        failed = conn.execute("SELECT COUNT(*) FROM deployments WHERE status='Failed'").fetchone()[0]
        running = conn.execute("SELECT COUNT(*) FROM deployments WHERE status='Running'").fetchone()[0]
    return render_template("index.html", deployments=deployments, total=total,
                           success=success, failed=failed, running=running)

@app.route("/deployments/new", methods=["POST"])
def add_deployment():
    project_name = request.form.get("project_name", "").strip()
    repository_url = request.form.get("repository_url", "").strip()
    environment = request.form.get("environment", "Development")
    status = request.form.get("status", "Queued")
    notes = request.form.get("notes", "").strip()

    if not project_name or not repository_url:
        flash("Project name and repository URL are required.", "error")
        return redirect(url_for("dashboard"))

    allowed_statuses = {"Queued", "Running", "Success", "Failed"}
    allowed_envs = {"Development", "Staging", "Production"}
    if status not in allowed_statuses or environment not in allowed_envs:
        flash("Please select a valid environment and status.", "error")
        return redirect(url_for("dashboard"))

    with get_db() as conn:
        conn.execute(
            """INSERT INTO deployments
            (project_name, repository_url, environment, status, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (project_name, repository_url, environment, status, notes,
             datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
    flash("Deployment record added.", "success")
    return redirect(url_for("dashboard"))

@app.route("/deployments/<int:deployment_id>/delete", methods=["POST"])
def delete_deployment(deployment_id):
    with get_db() as conn:
        conn.execute("DELETE FROM deployments WHERE id = ?", (deployment_id,))
    flash("Deployment record deleted.", "success")
    return redirect(url_for("dashboard"))

@app.route("/health")
def health():
    return {"status": "ok", "service": "DevOpsX"}, 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
