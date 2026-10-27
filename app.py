from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
import os
import secrets
import sqlite3
from datetime import datetime
from contextlib import contextmanager

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.abspath(os.environ.get("DEVOPSX_DB_PATH", os.path.join(BASE_DIR, "devopsx.db")))
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = bool(DATABASE_URL)

app = Flask(__name__)
if os.environ.get("RENDER") and not os.environ.get("DEVOPSX_SECRET"):
    raise RuntimeError("Missing DEVOPSX_SECRET: set it in the Render service environment.")
app.secret_key = os.environ.get("DEVOPSX_SECRET", "local-development-only-change-me")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),
)
ADMIN_USERNAME = os.environ.get("DEVOPSX_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("DEVOPSX_ADMIN_PASSWORD", "" if os.environ.get("RENDER") else "admin123")


def get_csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": get_csrf_token}


def csrf_protected(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        supplied = request.form.get("csrf_token", "")
        expected = session.get("_csrf_token", "")
        if not expected or not supplied or not secrets.compare_digest(supplied, expected):
            return "Invalid or missing CSRF token. Refresh the page and try again.", 400
        return view(*args, **kwargs)
    return wrapped


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def get_db():
    if USE_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row
        database_url = DATABASE_URL
        if database_url.startswith("postgres://"):
            database_url = "postgresql://" + database_url[len("postgres://"):]
        return psycopg.connect(database_url, row_factory=dict_row)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_connection():
    conn = get_db()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def execute(conn, sql, params=()):
    """Run parameterized SQL with the placeholder style for the selected database."""
    if USE_POSTGRES:
        sql = sql.replace("?", "%s")
    return conn.execute(sql, params)


def init_db():
    with db_connection() as conn:
        if USE_POSTGRES:
            execute(conn, """
                CREATE TABLE IF NOT EXISTS deployments (
                    id BIGSERIAL PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    repository_url TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)
        else:
            execute(conn, """
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

        count = execute(conn, "SELECT COUNT(*) AS count FROM deployments").fetchone()["count"]
        if count == 0:
            demo = [
                ("Campus Portal", "https://github.com/example/campus-portal", "Staging", "Success", "Demo deployment completed"),
                ("Library API", "https://github.com/example/library-api", "Production", "Failed", "Demo: missing environment variable"),
                ("Student Dashboard", "https://github.com/example/student-dashboard", "Development", "Running", "Demo deployment in progress"),
            ]
            # Insert rows separately so SQLite and PostgreSQL share the same code path.
            for project_name, repository_url, environment, status, notes in demo:
                execute(conn,
                    "INSERT INTO deployments (project_name, repository_url, environment, status, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (project_name, repository_url, environment, status, notes, datetime.now().strftime("%Y-%m-%d %H:%M"))
                )


# Initialize the database when the app starts under Gunicorn/production hosting.
init_db()


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        supplied_csrf = request.form.get("csrf_token", "")
        expected_csrf = session.get("_csrf_token", "")
        if not expected_csrf or not supplied_csrf or not secrets.compare_digest(supplied_csrf, expected_csrf):
            error = "Your session token expired. Refresh the page and try again."
        elif not ADMIN_PASSWORD:
            error = "Admin login is not configured. Set DEVOPSX_ADMIN_USERNAME and DEVOPSX_ADMIN_PASSWORD in the service environment."
        else:
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            if secrets.compare_digest(username, ADMIN_USERNAME) and secrets.compare_digest(password, ADMIN_PASSWORD):
                destination = request.args.get("next", "")
                session.clear()
                session["authenticated"] = True
                session["_csrf_token"] = secrets.token_urlsafe(32)
                if not destination.startswith("/") or destination.startswith("//"):
                    destination = url_for("dashboard")
                return redirect(destination)
            error = "Invalid username or password."
    return render_template("login.html", error=error), (503 if request.method == "POST" and not ADMIN_PASSWORD else 200)


@app.route("/logout", methods=["POST"])
@login_required
@csrf_protected
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    with db_connection() as conn:
        deployments = execute(conn, "SELECT * FROM deployments ORDER BY id DESC").fetchall()
        total = execute(conn, "SELECT COUNT(*) AS count FROM deployments").fetchone()["count"]
        success = execute(conn, "SELECT COUNT(*) AS count FROM deployments WHERE status='Success'").fetchone()["count"]
        failed = execute(conn, "SELECT COUNT(*) AS count FROM deployments WHERE status='Failed'").fetchone()["count"]
        running = execute(conn, "SELECT COUNT(*) AS count FROM deployments WHERE status='Running'").fetchone()["count"]
    return render_template("index.html", deployments=deployments, total=total,
                           success=success, failed=failed, running=running)


@app.route("/deployments/new", methods=["POST"])
@login_required
@csrf_protected
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

    with db_connection() as conn:
        execute(conn,
            """INSERT INTO deployments
            (project_name, repository_url, environment, status, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (project_name, repository_url, environment, status, notes,
             datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
    flash("Deployment record added.", "success")
    return redirect(url_for("dashboard"))


@app.route("/deployments/<int:deployment_id>/delete", methods=["POST"])
@login_required
@csrf_protected
def delete_deployment(deployment_id):
    with db_connection() as conn:
        execute(conn, "DELETE FROM deployments WHERE id = ?", (deployment_id,))
    flash("Deployment record deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/api/ci-status", methods=["POST"])
def ci_status():
    expected_token = os.environ.get("DEVOPSX_MONITOR_TOKEN", "")
    supplied_token = request.headers.get("Authorization", "")
    if not expected_token:
        return jsonify({"error": "CI status reporting is not configured"}), 503
    if not secrets.compare_digest(supplied_token, f"Bearer {expected_token}"):
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    if status not in {"Success", "Failed"}:
        return jsonify({"error": "status must be Success or Failed"}), 400

    run_url = str(payload.get("run_url", ""))[:500]
    commit_sha = str(payload.get("commit_sha", ""))[:100]
    notes = f"GitHub Actions CI: {status}"
    if commit_sha:
        notes += f" | commit: {commit_sha}"
    if run_url:
        notes += f" | run: {run_url}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    repo_url = "https://github.com/SwapnilPatil-1993/DevOpsX-Smart-Deployment-Dashboard"

    with db_connection() as conn:
        existing = execute(conn, "SELECT id FROM deployments WHERE project_name = ?", ("DevOpsX CI",)).fetchone()
        if existing:
            execute(conn,
                """UPDATE deployments
                   SET repository_url = ?, environment = ?, status = ?, notes = ?, created_at = ?
                   WHERE id = ?""",
                (repo_url, "Development", status, notes, now, existing["id"])
            )
        else:
            execute(conn,
                """INSERT INTO deployments
                   (project_name, repository_url, environment, status, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("DevOpsX CI", repo_url, "Development", status, notes, now)
            )
    return jsonify({"status": "recorded", "ci_status": status}), 200


@app.route("/health")
def health():
    # Check the actual database connection, not just whether DATABASE_URL exists.
    database_type = "postgresql" if USE_POSTGRES else "sqlite"
    try:
        with db_connection() as conn:
            execute(conn, "SELECT 1").fetchone()
        return {"status": "ok", "service": "DevOpsX", "database": database_type}, 200
    except Exception:
        app.logger.exception("Database health check failed")
        return {"status": "error", "service": "DevOpsX", "database": database_type}, 503


if __name__ == "__main__":
    app.run(debug=True)
