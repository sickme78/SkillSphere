"""Quiz storage. Quizzes live in the `quizzes` table instead of the browser cookie, so large
generated quizzes and their review data never hit the 4 KB session limit, and a submitted
quiz cannot be submitted twice for XP."""
import json

import db


def create(user_id, title, subject, source, questions):
    return db.q_exec(
        "INSERT INTO quizzes (user_id, title, subject, source, questions, total, created_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (user_id, title[:160], (subject or "")[:120], source, json.dumps(questions),
         len(questions), db.now_str()))


def _shape(row):
    if not row:
        return None
    row["questions"] = json.loads(row["questions"])
    row["result"] = json.loads(row["result"]) if row.get("result") else None
    return row


def get(quiz_id, user_id):
    if not quiz_id:
        return None
    return _shape(db.q_one("SELECT * FROM quizzes WHERE id=%s AND user_id=%s", (quiz_id, user_id)))


def save_result(quiz_id, score, review):
    return db.q_exec("UPDATE quizzes SET result=%s, score=%s, submitted_at=%s WHERE id=%s",
                     (json.dumps(review), score, db.now_str(), quiz_id))


def recent_scores(user_id, limit=6):
    """[(subject, percent)] newest first, from submitted quizzes."""
    rows = db.q_all("SELECT title, subject, score, total FROM quizzes WHERE user_id=%s AND "
                    "submitted_at IS NOT NULL ORDER BY id DESC LIMIT %s", (user_id, limit))
    return [((r["subject"] or r["title"]), round(r["score"] * 100 / r["total"]))
            for r in rows if r["total"]]
