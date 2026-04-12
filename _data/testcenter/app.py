"""Diagnostic Testcenter - Flask Web Application.

A digital test center for validated psychiatric screening instruments.
Supports bilingual tests (DE/EN), link sharing for remote completion,
automatic scoring, and print-friendly output.

Usage:
    python app.py                          # Start server (default: port 5000)
    TESTCENTER_PORT=8080 python app.py     # Custom port
    TESTCENTER_LANG=en python app.py       # Default English
"""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

from flask import (Flask, abort, g, jsonify, redirect, render_template,
                   request, url_for)

import config
import scoring as scoring_engine

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# First-start acknowledgement gate (MDR-Abgrenzung).
# Registers /disclaimer and a before_request hook that redirects users
# there until they confirm the four mandatory items.
try:
    from disclaimer import register_disclaimer  # type: ignore
    register_disclaimer(app)
except ImportError:
    logging.getLogger(__name__).warning(
        "Disclaimer module not found — gate disabled. "
        "README/NOTICE still apply."
    )

import logging
import traceback as _tb
logging.basicConfig(level=logging.DEBUG, force=True)
logger = logging.getLogger(__name__)


@app.errorhandler(Exception)
def _handle_error(e):
    logger.error("Unhandled exception: %s\n%s", e, _tb.format_exc())
    return f"<pre>{_tb.format_exc()}</pre>", 500

_db_initialized = False

@app.before_request
def _ensure_db():
    """Ensure database tables exist on first request."""
    global _db_initialized
    if not _db_initialized:
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                test_id TEXT NOT NULL,
                client_name TEXT DEFAULT '',
                language TEXT DEFAULT 'de',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT DEFAULT 'pending',
                responses TEXT DEFAULT '{}',
                scores TEXT DEFAULT '{}',
                notes TEXT DEFAULT '',
                battery_id TEXT DEFAULT ''
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS batteries (
                id TEXT PRIMARY KEY,
                client_name TEXT DEFAULT '',
                language TEXT DEFAULT 'de',
                test_ids TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending'
            )
        """)
        # Migration: add battery_id column if missing
        cols = [r[1] for r in db.execute("PRAGMA table_info(sessions)").fetchall()]
        if "battery_id" not in cols:
            db.execute("ALTER TABLE sessions ADD COLUMN battery_id TEXT DEFAULT ''")
        db.commit()
        _db_initialized = True

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(config.DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            test_id TEXT NOT NULL,
            client_name TEXT DEFAULT '',
            language TEXT DEFAULT 'de',
            created_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT DEFAULT 'pending',
            responses TEXT DEFAULT '{}',
            scores TEXT DEFAULT '{}',
            notes TEXT DEFAULT ''
        )
    """)
    db.commit()


# ---------------------------------------------------------------------------
# Test loader
# ---------------------------------------------------------------------------

_tests_cache: dict[str, dict] = {}


def load_tests() -> dict[str, dict]:
    """Load all test definitions from JSON files."""
    global _tests_cache
    if _tests_cache:
        return _tests_cache

    for filename in sorted(os.listdir(config.TESTS_DIR)):
        if filename.endswith(".json"):
            path = os.path.join(config.TESTS_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                test_def = json.load(f)
                _tests_cache[test_def["id"]] = test_def

    return _tests_cache


def get_test(test_id: str) -> dict | None:
    tests = load_tests()
    return tests.get(test_id)


def t(obj, lang="de"):
    """Extract localized text from a bilingual dict."""
    if isinstance(obj, dict):
        return obj.get(lang, obj.get("de", obj.get("en", str(obj))))
    return str(obj) if obj else ""


# ---------------------------------------------------------------------------
# Routes: Dashboard & Test Catalog
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    lang = request.args.get("lang", config.DEFAULT_LANG)
    tests = load_tests()

    # Group tests by domain/axis
    grouped = {}
    for tid, tdef in tests.items():
        axis = tdef.get("axis", "?")
        key = {
            "I": ("Achse I: Psychische Störungen", "Axis I: Mental Disorders"),
            "II": ("Achse II: Persönlichkeit", "Axis II: Personality"),
            "IV": ("Achse IV: Funktionalität", "Axis IV: Functioning"),
        }.get(axis, ("Sonstige", "Other"))
        label = key[0] if lang == "de" else key[1]
        grouped.setdefault(label, []).append(tdef)

    # Recent sessions
    db = get_db()
    recent = db.execute(
        "SELECT * FROM sessions ORDER BY created_at DESC LIMIT 20"
    ).fetchall()

    return render_template("index.html", grouped=grouped, recent=recent,
                           lang=lang, t=t, tests=tests)


@app.route("/tests")
def test_list():
    lang = request.args.get("lang", config.DEFAULT_LANG)
    tests = load_tests()
    return render_template("test_list.html", tests=tests, lang=lang, t=t)


@app.route("/tests/<test_id>")
def test_detail(test_id):
    lang = request.args.get("lang", config.DEFAULT_LANG)
    tdef = get_test(test_id)
    if not tdef:
        abort(404)
    return render_template("test_detail.html", test=tdef, lang=lang, t=t)


# ---------------------------------------------------------------------------
# Routes: Print-friendly blank test (single + bulk)
# ---------------------------------------------------------------------------

@app.route("/tests/print-bundle")
def print_bundle():
    """Print multiple tests as a single document for pen & paper use."""
    lang = request.args.get("lang", config.DEFAULT_LANG)
    test_ids = request.args.getlist("t")
    if not test_ids:
        abort(400)
    tests_list = []
    for tid in test_ids:
        tdef = get_test(tid)
        if tdef:
            tests_list.append(tdef)
    if not tests_list:
        abort(404)
    return render_template("print_bundle.html", tests_list=tests_list, lang=lang, t=t)


# ---------------------------------------------------------------------------
# Routes: Test batteries (multiple tests for one client)
# ---------------------------------------------------------------------------

@app.route("/batteries/create", methods=["GET", "POST"])
def create_battery():
    lang = request.args.get("lang", config.DEFAULT_LANG)
    tests = load_tests()

    if request.method == "POST":
        selected = request.form.getlist("test_ids")
        client_name = request.form.get("client_name", "")
        bat_lang = request.form.get("language", lang)

        if not selected:
            return render_template("create_battery.html", tests=tests,
                                   lang=lang, t=t, error=True)

        bat_id = str(uuid.uuid4())[:12]
        now = datetime.now(timezone.utc).isoformat()

        db = get_db()
        db.execute(
            "INSERT INTO batteries (id, client_name, language, test_ids, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (bat_id, client_name, bat_lang, json.dumps(selected), now)
        )

        # Create individual sessions for each test, linked to battery
        for tid in selected:
            token = str(uuid.uuid4())[:12]
            db.execute(
                "INSERT INTO sessions (id, test_id, client_name, language, "
                "created_at, status, battery_id) VALUES (?, ?, ?, ?, ?, 'pending', ?)",
                (token, tid, client_name, bat_lang, now, bat_id)
            )
        db.commit()

        return redirect(url_for("view_battery", battery_id=bat_id, lang=lang))

    # Pre-select tests if passed as query params
    preselected = request.args.getlist("t")
    return render_template("create_battery.html", tests=tests, lang=lang, t=t,
                           preselected=preselected, error=False)


@app.route("/b/<battery_id>")
def view_battery(battery_id):
    """Battery overview: client sees all tests, picks next incomplete one."""
    db = get_db()
    battery = db.execute(
        "SELECT * FROM batteries WHERE id = ?", (battery_id,)
    ).fetchone()
    if not battery:
        abort(404)

    lang = battery["language"]
    sessions = db.execute(
        "SELECT * FROM sessions WHERE battery_id = ? ORDER BY rowid",
        (battery_id,)
    ).fetchall()

    tests = load_tests()
    session_info = []
    all_done = True
    next_token = None
    for s in sessions:
        tdef = tests.get(s["test_id"])
        info = {
            "token": s["id"],
            "test_id": s["test_id"],
            "abbreviation": tdef["abbreviation"] if tdef else s["test_id"],
            "name": t(tdef["name"], lang) if tdef else "",
            "status": s["status"],
            "items": len(tdef.get("items", [])) if tdef else 0,
        }
        if s["status"] != "completed":
            all_done = False
            if next_token is None:
                next_token = s["id"]
        session_info.append(info)

    # Update battery status
    if all_done and battery["status"] != "completed":
        db.execute("UPDATE batteries SET status='completed' WHERE id=?",
                   (battery_id,))
        db.commit()

    return render_template("battery_view.html", battery=battery,
                           sessions=session_info, lang=lang, t=t,
                           all_done=all_done, next_token=next_token,
                           battery_id=battery_id)


@app.route("/batteries/<battery_id>/results")
def battery_results(battery_id):
    """Clinician view: all results for a battery."""
    lang = request.args.get("lang", config.DEFAULT_LANG)
    db = get_db()
    battery = db.execute(
        "SELECT * FROM batteries WHERE id = ?", (battery_id,)
    ).fetchone()
    if not battery:
        abort(404)

    sessions = db.execute(
        "SELECT * FROM sessions WHERE battery_id = ? ORDER BY rowid",
        (battery_id,)
    ).fetchall()

    tests = load_tests()
    results = []
    for s in sessions:
        tdef = tests.get(s["test_id"])
        scores = json.loads(s["scores"]) if s["scores"] else {}
        results.append({
            "token": s["id"],
            "test": tdef,
            "session": s,
            "scores": scores,
        })

    return render_template("battery_results.html", battery=battery,
                           results=results, lang=lang, t=t)

@app.route("/tests/<test_id>/print")
@app.route("/tests/<test_id>/print/<lang>")
def print_test(test_id, lang=None):
    if lang is None:
        lang = request.args.get("lang", config.DEFAULT_LANG)
    tdef = get_test(test_id)
    if not tdef:
        abort(404)
    return render_template("print_test.html", test=tdef, lang=lang, t=t)


# ---------------------------------------------------------------------------
# Routes: Session management (clinician creates, client fills)
# ---------------------------------------------------------------------------

@app.route("/sessions/create", methods=["GET", "POST"])
def create_session():
    lang = request.args.get("lang", config.DEFAULT_LANG)
    tests = load_tests()

    if request.method == "POST":
        test_id = request.form.get("test_id", "")
        client_name = request.form.get("client_name", "")
        session_lang = request.form.get("language", lang)

        if test_id not in tests:
            abort(400)

        token = str(uuid.uuid4())[:12]
        now = datetime.now(timezone.utc).isoformat()

        db = get_db()
        db.execute(
            "INSERT INTO sessions (id, test_id, client_name, language, created_at, status) "
            "VALUES (?, ?, ?, ?, ?, 'pending')",
            (token, test_id, client_name, session_lang, now)
        )
        db.commit()

        return render_template("session_created.html",
                               token=token, test=tests[test_id],
                               client_name=client_name, lang=lang, t=t,
                               base_url=request.host_url.rstrip("/"))

    return render_template("create_session.html", tests=tests, lang=lang, t=t)


# ---------------------------------------------------------------------------
# Routes: Client-facing test form
# ---------------------------------------------------------------------------

@app.route("/s/<token>", methods=["GET", "POST"])
def client_test(token):
    db = get_db()
    session = db.execute("SELECT * FROM sessions WHERE id = ?", (token,)).fetchone()

    if not session:
        abort(404)

    lang = session["language"]
    tdef = get_test(session["test_id"])
    if not tdef:
        abort(500)

    # Check expiry
    if config.SESSION_EXPIRY_HOURS > 0:
        created = datetime.fromisoformat(session["created_at"])
        if datetime.now(timezone.utc) > created + timedelta(hours=config.SESSION_EXPIRY_HOURS):
            return render_template("session_expired.html", lang=lang, t=t)

    # Already completed
    if session["status"] == "completed":
        return render_template("test_complete.html", test=tdef, lang=lang, t=t,
                               already_completed=True)

    if request.method == "POST":
        # Collect responses
        responses = {}
        for item in tdef.get("items", []):
            key = str(item["number"])
            # Standard response
            val = request.form.get(f"item_{key}")
            if val is not None:
                responses[key] = int(val)

            # Endorsement + distress (PQ-16 style)
            endorse_val = request.form.get(f"item_{key}_endorsed")
            if endorse_val is not None:
                responses[f"{key}_endorsed"] = int(endorse_val)
                distress_val = request.form.get(f"item_{key}_distress", 0)
                responses[f"{key}_distress"] = int(distress_val)

        # Supplementary item (PHQ-9)
        supp = request.form.get("supplementary")
        if supp is not None:
            responses["supplementary"] = int(supp)

        # Score
        scores = scoring_engine.score_test(tdef, responses)

        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "UPDATE sessions SET status='completed', completed_at=?, "
            "responses=?, scores=? WHERE id=?",
            (now, json.dumps(responses), json.dumps(scores, default=str), token)
        )
        db.commit()

        # If part of a battery, redirect to battery overview
        battery_id = session["battery_id"] if session["battery_id"] else ""
        if battery_id:
            return redirect(url_for("view_battery", battery_id=battery_id))

        return render_template("test_complete.html", test=tdef, lang=lang, t=t,
                               already_completed=False)

    return render_template("test_form.html", test=tdef, lang=lang, t=t,
                           token=token, client_name=session["client_name"])


# ---------------------------------------------------------------------------
# Routes: Results (clinician view)
# ---------------------------------------------------------------------------

@app.route("/results/<token>")
def view_results(token):
    lang = request.args.get("lang", config.DEFAULT_LANG)
    db = get_db()
    session = db.execute("SELECT * FROM sessions WHERE id = ?", (token,)).fetchone()

    if not session:
        abort(404)

    tdef = get_test(session["test_id"])
    responses = json.loads(session["responses"]) if session["responses"] else {}
    scores = json.loads(session["scores"]) if session["scores"] else {}

    return render_template("result.html", test=tdef, session=session,
                           responses=responses, scores=scores, lang=lang, t=t)


@app.route("/results/<token>/print")
def print_results(token):
    lang = request.args.get("lang", config.DEFAULT_LANG)
    db = get_db()
    session = db.execute("SELECT * FROM sessions WHERE id = ?", (token,)).fetchone()

    if not session:
        abort(404)

    tdef = get_test(session["test_id"])
    responses = json.loads(session["responses"]) if session["responses"] else {}
    scores = json.loads(session["scores"]) if session["scores"] else {}

    return render_template("result_print.html", test=tdef, session=session,
                           responses=responses, scores=scores, lang=lang, t=t)


# ---------------------------------------------------------------------------
# Routes: Delete session
# ---------------------------------------------------------------------------

@app.route("/results/<token>/delete", methods=["GET", "POST"])
def delete_session(token):
    lang = request.args.get("lang", config.DEFAULT_LANG)
    db = get_db()
    session = db.execute("SELECT * FROM sessions WHERE id = ?", (token,)).fetchone()

    if not session:
        abort(404)

    tdef = get_test(session["test_id"])

    if request.method == "POST":
        confirm = request.form.get("confirm", "")
        if confirm == token:
            db.execute("DELETE FROM sessions WHERE id = ?", (token,))
            db.commit()
            return redirect(url_for("index", lang=lang, deleted="1"))

    return render_template("confirm_delete.html", session=session,
                           test=tdef, lang=lang, t=t)


@app.route("/api/sessions/<token>", methods=["DELETE"])
def api_delete_session(token):
    """Delete a session via API."""
    db = get_db()
    session = db.execute("SELECT * FROM sessions WHERE id = ?", (token,)).fetchone()
    if not session:
        abort(404)
    db.execute("DELETE FROM sessions WHERE id = ?", (token,))
    db.commit()
    return jsonify({"deleted": token, "status": "ok"})


# ---------------------------------------------------------------------------
# API endpoints (for integration with multiaxial_diagnostic_system)
# ---------------------------------------------------------------------------

@app.route("/api/tests")
def api_tests():
    tests = load_tests()
    return jsonify([{
        "id": tid,
        "name": tdef["name"],
        "abbreviation": tdef["abbreviation"],
        "domain": tdef.get("domain", {}),
        "axis": tdef.get("axis"),
        "items_count": len(tdef.get("items", [])),
        "clinical_cutoff": tdef.get("scoring", {}).get("clinical_cutoff")
    } for tid, tdef in tests.items()])


@app.route("/api/tests/<test_id>")
def api_test_detail(test_id):
    tdef = get_test(test_id)
    if not tdef:
        abort(404)
    return jsonify(tdef)


@app.route("/api/results/<token>")
def api_results(token):
    db = get_db()
    session = db.execute("SELECT * FROM sessions WHERE id = ?", (token,)).fetchone()
    if not session:
        abort(404)

    return jsonify({
        "token": token,
        "test_id": session["test_id"],
        "client_name": session["client_name"],
        "status": session["status"],
        "created_at": session["created_at"],
        "completed_at": session["completed_at"],
        "responses": json.loads(session["responses"]) if session["responses"] else {},
        "scores": json.loads(session["scores"]) if session["scores"] else {}
    })


@app.route("/api/score", methods=["POST"])
def api_score():
    """Score a test without creating a session (for programmatic use)."""
    data = request.get_json()
    if not data:
        abort(400)

    test_id = data.get("test_id")
    responses = data.get("responses", {})

    tdef = get_test(test_id)
    if not tdef:
        abort(404)

    scores = scoring_engine.score_test(tdef, responses)
    return jsonify(scores)


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

@app.context_processor
def inject_helpers():
    return {
        "now": datetime.now(timezone.utc),
        "config": config,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    os.makedirs(config.SESSIONS_DIR, exist_ok=True)
    os.makedirs(config.PDFS_DIR, exist_ok=True)

    with app.app_context():
        init_db()

    print(f"Diagnostic Testcenter starting on http://{config.HOST}:{config.PORT}")
    print(f"Default language: {config.DEFAULT_LANG}")
    print(f"Tests loaded: {len(load_tests())}")

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
