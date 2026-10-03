"""
MySQL access layer.

If MySQL is not reachable, the app falls back to an in-memory store so the
demo never crashes during a presentation. The fallback is clearly flagged in
the UI (see the banner in base.html).
"""
import os
import sqlite3
import threading
from datetime import datetime

import mysql.connector
from mysql.connector import Error

import db_schema

_MEMORY = {"profiles": {}, "results": {}, "next_id": 1}
LAST_ERROR = None


def _config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "skillsphere"),
    }


def get_conn():
    """Return a live MySQL connection, or None if the database is unavailable."""
    global LAST_ERROR
    try:
        conn = mysql.connector.connect(connection_timeout=4, **_config())
        LAST_ERROR = None
        return conn
    except Error as exc:
        LAST_ERROR = str(exc)
        return None


def using_mysql():
    conn = get_conn()
    if conn:
        conn.close()
        return True
    return False


# ---------- profiles ----------

def save_profile(p):
    conn = get_conn()
    if not conn:
        pid = _MEMORY["next_id"]
        _MEMORY["next_id"] += 1
        p = dict(p, id=pid)
        _MEMORY["profiles"][pid] = p
        return pid
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE name = VALUES(name), id = LAST_INSERT_ID(id)",
            (p["name"], p["email"]),
        )
        user_id = cur.lastrowid
        cur.execute(
            """INSERT INTO profiles (user_id, education, experience, current_skills, learning_goal, target_role)
               VALUES (%s,%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE education=VALUES(education), experience=VALUES(experience),
                 current_skills=VALUES(current_skills), learning_goal=VALUES(learning_goal),
                 target_role=VALUES(target_role)""",
            (user_id, p["education"], p["experience"], p["current_skills"],
             p["learning_goal"], p["target_role"]),
        )
        conn.commit()
        return user_id
    except Error:
        return None
    finally:
        conn.close()


def get_profile(user_id):
    if not user_id:
        return None
    conn = get_conn()
    if not conn:
        return _MEMORY["profiles"].get(user_id)
    try:
        cur = conn.cursor(dictionary=True, buffered=True)
        cur.execute(
            """SELECT u.id, u.name, u.email, p.education, p.experience, p.current_skills,
                      p.learning_goal, p.target_role
               FROM users u JOIN profiles p ON p.user_id = u.id WHERE u.id = %s""",
            (user_id,),
        )
        return cur.fetchone()
    except Error:
        return None
    finally:
        conn.close()


# ---------- quiz results ----------

def save_quiz_result(user_id, title, score, total, answers):
    """answers: list of dicts with question, user_answer, correct_answer, is_correct"""
    conn = get_conn()
    if not conn:
        row = {"id": len(_MEMORY["results"]) + 1, "quiz_title": title, "score": score,
               "total": total, "taken_at": datetime.now()}
        _MEMORY["results"].setdefault(user_id, []).insert(0, row)
        return row["id"]
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO quiz_results (user_id, quiz_title, score, total) VALUES (%s,%s,%s,%s)",
            (user_id, title, score, total),
        )
        result_id = cur.lastrowid
        for a in answers:
            cur.execute(
                """INSERT INTO quiz_answers (result_id, question, user_answer, correct_answer, is_correct)
                   VALUES (%s,%s,%s,%s,%s)""",
                (result_id, a["question"][:500], a["user_answer"], a["correct_answer"], int(a["is_correct"])),
            )
        conn.commit()
        return result_id
    except Error:
        return None
    finally:
        conn.close()


def get_quiz_results(user_id, limit=5):
    if not user_id:
        return []
    conn = get_conn()
    if not conn:
        return _MEMORY["results"].get(user_id, [])[:limit]
    try:
        cur = conn.cursor(dictionary=True, buffered=True)
        cur.execute(
            "SELECT id, quiz_title, score, total, taken_at FROM quiz_results "
            "WHERE user_id=%s ORDER BY taken_at DESC LIMIT %s",
            (user_id, limit),
        )
        return cur.fetchall()
    except Error:
        return []
    finally:
        conn.close()


# =====================================================================
# Shared query helpers for the learning-platform tables (quizzes, problems,
# learning_activity, badges ...). They talk to MySQL when it is reachable and to an
# in-memory SQLite database (same tables) when it is not, so the demo never breaks.
# Write SQL with %s placeholders; they are translated for SQLite automatically.
# =====================================================================
_LITE = None
_LITE_LOCK = threading.RLock()
_MYSQL_READY = False
_LITE_READY = False
SQL_ERROR = None


def _lite():
    global _LITE
    if _LITE is None:
        _LITE = sqlite3.connect(":memory:", check_same_thread=False)
        _LITE.row_factory = sqlite3.Row
    return _LITE


def _bootstrap(run):
    """Create tables (idempotent) and seed reference data via run(sql, params)."""
    import gamification
    import problems
    problems.seed(run)
    gamification.seed(run)


def _ensure_mysql(conn):
    global _MYSQL_READY
    if _MYSQL_READY:
        return
    cur = conn.cursor()
    for stmt in db_schema.ddl("mysql"):
        cur.execute(stmt)
    conn.commit()
    _bootstrap_mysql(conn)
    _MYSQL_READY = True


def _bootstrap_mysql(conn):
    def run(sql, params=()):
        cur = conn.cursor(dictionary=True, buffered=True)
        cur.execute(sql, params)
        rows = cur.fetchall() if cur.with_rows else []
        conn.commit()
        return rows
    _bootstrap(run)


def _ensure_lite():
    global _LITE_READY
    if _LITE_READY:
        return
    lite = _lite()
    for stmt in db_schema.ddl("sqlite"):
        lite.execute(stmt)
    lite.commit()

    def run(sql, params=()):
        cur = lite.execute(sql.replace("%s", "?"), params)
        rows = [dict(r) for r in cur.fetchall()] if cur.description else []
        lite.commit()
        return rows
    _bootstrap(run)
    _LITE_READY = True


def _execute(sql, params, fetch):
    """fetch: 'all' | 'one' | None. Returns rows / row / lastrowid, or None on error."""
    global SQL_ERROR
    conn = get_conn()
    try:
        if conn:
            _ensure_mysql(conn)
            cur = conn.cursor(dictionary=True, buffered=True)
            cur.execute(sql, params)
            if fetch == "all":
                return cur.fetchall()
            if fetch == "one":
                return cur.fetchone()
            conn.commit()
            return cur.lastrowid or True
        with _LITE_LOCK:
            _ensure_lite()
            lite = _lite()
            cur = lite.execute(sql.replace("%s", "?"), params)
            if fetch == "all":
                return [dict(r) for r in cur.fetchall()]
            if fetch == "one":
                row = cur.fetchone()
                return dict(row) if row else None
            lite.commit()
            return cur.lastrowid or True
    except (Error, sqlite3.Error) as exc:
        SQL_ERROR = str(exc)
        print("[SkillSphere] SQL error: %s" % exc)
        return [] if fetch == "all" else None
    finally:
        if conn:
            conn.close()


def q_all(sql, params=()):
    return _execute(sql, params, "all") or []


def q_one(sql, params=()):
    return _execute(sql, params, "one")


def q_exec(sql, params=()):
    """INSERT / UPDATE / DELETE. Returns the new row id (or True), None on failure."""
    return _execute(sql, params, None)


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def as_dt(value):
    """MySQL returns datetime, SQLite returns text - normalise to datetime."""
    if isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.now()
