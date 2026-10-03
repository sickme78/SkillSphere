"""XP, levels, badges and learning streaks.

Design choice: there is ONE source of truth - the `learning_activity` table. Every
real learning action (finishing a quiz, solving a problem, completing a learning task)
writes a row there. XP, level, streak and most badges are derived from those rows, so
they can never drift out of sync. Merely opening a page writes nothing.
"""
import json
from datetime import date, datetime, timedelta

import db

# ---------------------------------------------------------------- rules
XP_QUIZ_COMPLETE = 50
XP_QUIZ_HIGH_SCORE = 100        # extra, when the score is 80% or more
XP_PRACTICE_PROBLEM = 25        # a problem solved outside "Problem of the Day"
XP_LEARNING_TASK = 75
STREAK_BONUS_PER_DAY = 5        # bonus = this x streak length (streak capped at 7)
MAX_XP_QUIZZES_PER_DAY = 5      # quizzes beyond this are saved but earn no XP
HIGH_SCORE_PERCENT = 80

# (level, name, xp needed to reach it)
LEVELS = [(1, "Explorer", 0), (2, "Learner", 150), (3, "Builder", 400),
          (4, "Achiever", 1000), (5, "Skill Master", 2000)]

# Activity types that count as real learning (and therefore keep a streak alive).
LEARNING_TYPES = ("quiz", "problem", "learning_task")

BADGES = [
    ("first_quiz", "First Quiz", "Completed your first quiz.", "Q"),
    ("first_problem", "First Problem", "Solved your first problem.", "P"),
    ("streak_7", "7 Day Streak", "Learned on 7 days in a row.", "7"),
    ("quizzes_10", "10 Quizzes Completed", "Finished ten quizzes.", "10"),
    ("perfect_score", "Perfect Score", "Scored 100% on a quiz.", "100"),
    ("skill_completed", "Skill Completed", "Completed a learning task for a skill.", "\u2713"),
    ("problem_solver", "Problem Solver", "Solved five problems.", "5P"),
]


def seed(run):
    existing = {r["code"] for r in run("SELECT code FROM badges")}
    for code, name, desc, glyph in BADGES:
        if code not in existing:
            run("INSERT INTO badges (code, name, description, glyph) VALUES (%s,%s,%s,%s)",
                (code, name, desc, glyph))


# ---------------------------------------------------------------- reading activity
def _rows(user_id):
    rows = db.q_all(
        "SELECT id, activity_type, title, ref, xp, detail, activity_date, created_at "
        "FROM learning_activity WHERE user_id=%s ORDER BY id DESC", (user_id,))
    for r in rows:
        r["activity_date"] = str(r["activity_date"])[:10]
        r["created_at"] = db.as_dt(r["created_at"])
        try:
            r["detail"] = json.loads(r["detail"]) if r["detail"] else {}
        except ValueError:
            r["detail"] = {}
    return rows


def level_for(xp):
    current = LEVELS[0]
    for lvl in LEVELS:
        if xp >= lvl[2]:
            current = lvl
    return current


def streaks(rows, today=None):
    """(current, longest, active_today) from the days on which real learning happened."""
    today = today or date.today()
    days = sorted({date.fromisoformat(r["activity_date"]) for r in rows
                   if r["activity_type"] in LEARNING_TYPES})
    if not days:
        return 0, 0, False
    longest = run = 1
    for prev, cur in zip(days, days[1:]):
        run = run + 1 if (cur - prev).days == 1 else 1
        longest = max(longest, run)
    active_today = days[-1] == today
    # The streak stays alive until a whole day is missed: today OR yesterday may be the last day.
    current = 0
    if days[-1] >= today - timedelta(days=1):
        current = 1
        for i in range(len(days) - 1, 0, -1):
            if (days[i] - days[i - 1]).days == 1:
                current += 1
            else:
                break
    return current, longest, active_today


def summary(user_id, rows=None):
    """Everything the UI needs about progress, from one query."""
    rows = _rows(user_id) if rows is None else rows
    xp = sum(r["xp"] for r in rows)
    num, name, start = level_for(xp)
    nxt = next((l for l in LEVELS if l[0] == num + 1), None)
    if nxt:
        pct = round((xp - start) * 100 / (nxt[2] - start))
        target = nxt[2]
    else:
        pct, target = 100, xp
    current, longest, active_today = streaks(rows)
    return {"xp": xp, "level": num, "level_name": name, "level_start": start,
            "next_target": target, "next_name": nxt[1] if nxt else None, "percent": pct,
            "streak": current, "longest_streak": longest, "active_today": active_today,
            "badge_count": len(earned_badges(user_id))}


def earned_badges(user_id):
    rows = db.q_all(
        "SELECT b.code, b.name, b.description, b.glyph, ub.earned_at FROM user_badges ub "
        "JOIN badges b ON b.code = ub.badge_code WHERE ub.user_id=%s ORDER BY ub.id", (user_id,))
    return rows


def all_badges(user_id):
    """Every badge with an `earned` flag, for the badge shelf."""
    got = {b["code"] for b in earned_badges(user_id)}
    out = [dict(code=c, name=n, description=d, glyph=g, earned=c in got) for c, n, d, g in BADGES]
    return out


def recent_activity(user_id, limit=6, rows=None):
    rows = _rows(user_id) if rows is None else rows
    feed = []
    for r in rows:
        if r["activity_type"] == "streak_bonus":
            continue
        d = r["detail"]
        if r["activity_type"] == "quiz":
            title = r["title"]
            meta = "%s%%" % d.get("percent", "?")
        elif r["activity_type"] == "problem":
            title = r["title"]
            meta = "Completed"
        else:
            title = r["title"]
            meta = "Completed"
        feed.append({"title": title, "meta": meta, "xp": r["xp"], "type": r["activity_type"],
                     "when": r["created_at"]})
        if len(feed) >= limit:
            break
    return feed


def weak_topics(user_id, rows=None, last_n=5):
    """Topics missed most often across the last few quizzes: [(topic, misses)]."""
    rows = _rows(user_id) if rows is None else rows
    counts = {}
    seen = 0
    for r in rows:
        if r["activity_type"] != "quiz":
            continue
        for t in r["detail"].get("weak", []):
            counts[t] = counts.get(t, 0) + 1
        seen += 1
        if seen >= last_n:
            break
    return sorted(counts.items(), key=lambda kv: -kv[1])


# ---------------------------------------------------------------- writing activity
def _log(user_id, kind, title, xp, ref=None, detail=None):
    now = datetime.now()
    return db.q_exec(
        "INSERT INTO learning_activity (user_id, activity_type, title, ref, xp, detail, "
        "activity_date, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (user_id, kind, title[:200], ref, xp, json.dumps(detail) if detail else None,
         now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d %H:%M:%S")))


def _finish(user_id, before_xp, base_xp, notes):
    """Streak bonus + badges + level-up detection after a learning action was logged."""
    rows = _rows(user_id)
    current, _, _ = streaks(rows)
    today = date.today().isoformat()
    bonus = 0
    if current >= 2 and not any(r["activity_type"] == "streak_bonus" and r["activity_date"] == today
                                for r in rows):
        bonus = STREAK_BONUS_PER_DAY * min(current, 7)
        _log(user_id, "streak_bonus", "%d-day streak bonus" % current, bonus)
        rows = _rows(user_id)
        notes.append("%d-day streak bonus +%d XP" % (current, bonus))
    new_badges = award_badges(user_id, rows)
    after = sum(r["xp"] for r in rows)
    level_up = level_for(after)[0] > level_for(before_xp)[0]
    return {"xp": base_xp + bonus, "badges": new_badges, "level_up": level_for(after) if level_up else None,
            "notes": notes}


def award_badges(user_id, rows=None):
    rows = _rows(user_id) if rows is None else rows
    have = {b["code"] for b in earned_badges(user_id)}
    quizzes = [r for r in rows if r["activity_type"] == "quiz"]
    problems = [r for r in rows if r["activity_type"] == "problem"]
    tasks = [r for r in rows if r["activity_type"] == "learning_task"]
    _, longest, _ = streaks(rows)
    checks = {
        "first_quiz": len(quizzes) >= 1,
        "quizzes_10": len(quizzes) >= 10,
        "perfect_score": any(q["detail"].get("percent") == 100 for q in quizzes),
        "first_problem": len(problems) >= 1,
        "problem_solver": len(problems) >= 5,
        "skill_completed": len(tasks) >= 1,
        "streak_7": longest >= 7,
    }
    names = {c: n for c, n, _, _ in BADGES}
    new = []
    for code, ok in checks.items():
        if ok and code not in have:
            if db.q_exec("INSERT INTO user_badges (user_id, badge_code, earned_at) VALUES (%s,%s,%s)",
                         (user_id, code, db.now_str())):
                new.append(names[code])
    return new


def on_quiz_completed(user_id, title, subject, score, total, weak, strong, quiz_id):
    rows = _rows(user_id)
    before = sum(r["xp"] for r in rows)
    today = date.today().isoformat()
    todays_quizzes = sum(1 for r in rows if r["activity_type"] == "quiz" and r["activity_date"] == today
                         and r["xp"] > 0)
    percent = round(score * 100 / total) if total else 0
    xp, notes = 0, []
    if todays_quizzes < MAX_XP_QUIZZES_PER_DAY:
        xp = XP_QUIZ_COMPLETE
        notes.append("Quiz completed +%d XP" % XP_QUIZ_COMPLETE)
        if percent >= HIGH_SCORE_PERCENT:
            xp += XP_QUIZ_HIGH_SCORE
            notes.append("Score of %d%%+ +%d XP" % (HIGH_SCORE_PERCENT, XP_QUIZ_HIGH_SCORE))
    else:
        notes.append("Daily quiz XP limit reached - this quiz was saved without XP.")
    _log(user_id, "quiz", "%s Quiz" % (subject or title), xp, ref=str(quiz_id),
         detail={"percent": percent, "score": score, "total": total, "subject": subject or title,
                 "weak": weak, "strong": strong})
    return _finish(user_id, before, xp, notes)


def on_problem_solved(user_id, problem, is_daily):
    """Returns None if this problem was already solved by the user (no double XP)."""
    if db.q_one("SELECT id FROM problem_solves WHERE user_id=%s AND problem_id=%s",
                (user_id, problem["id"])):
        return None
    rows = _rows(user_id)
    before = sum(r["xp"] for r in rows)
    xp = problem["xp_reward"] if is_daily else XP_PRACTICE_PROBLEM
    ok = db.q_exec("INSERT INTO problem_solves (user_id, problem_id, xp_awarded, solved_at) "
                   "VALUES (%s,%s,%s,%s)", (user_id, problem["id"], xp, db.now_str()))
    if not ok:
        return None
    label = "Problem of the Day" if is_daily else "Practice"
    _log(user_id, "problem", "%s \u2014 %s" % (label, problem["title"]), xp, ref=str(problem["id"]),
         detail={"daily": is_daily, "domain": problem["domain"], "topic": problem["topic"]})
    notes = ["%s solved +%d XP" % ("Problem of the Day" if is_daily else "Problem", xp)]
    return _finish(user_id, before, xp, notes)


def on_learning_task_completed(user_id, skill):
    """Returns None if the learner already completed this skill's task."""
    if db.q_one("SELECT id FROM learning_activity WHERE user_id=%s AND activity_type='learning_task' "
                "AND ref=%s", (user_id, skill)):
        return None
    rows = _rows(user_id)
    before = sum(r["xp"] for r in rows)
    _log(user_id, "learning_task", "Learned %s" % skill, XP_LEARNING_TASK, ref=skill,
         detail={"skill": skill})
    return _finish(user_id, before, XP_LEARNING_TASK,
                   ["Learning task completed +%d XP" % XP_LEARNING_TASK])


def flash_lines(result):
    """Turn an event result into short messages for flash()."""
    if not result:
        return []
    lines = list(result["notes"])
    if result["level_up"]:
        lines.append("Level up! You are now Level %d \u2014 %s." % (result["level_up"][0], result["level_up"][1]))
    for b in result["badges"]:
        lines.append("Badge earned: %s" % b)
    return lines


def activity_rows(user_id):
    """Public accessor for the learner's full activity log (newest first)."""
    return _rows(user_id)
