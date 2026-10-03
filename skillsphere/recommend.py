"""Connects the pieces: skill gaps + quiz performance + practice + XP -> one next step.

The loop this drives:  ASSESS -> IDENTIFY GAP -> LEARN -> PRACTICE -> QUIZ -> IMPROVE -> EARN XP.
Everything here is rule-based and explainable on purpose.
"""
from flask import url_for

import data
import gamification
import problems
import quizzes

# Quiz subjects people commonly upload -> the role skills they evidence.
SUBJECT_SKILLS = {
    "dbms": ["SQL", "Database Design"], "database": ["SQL", "Database Design"],
    "sql": ["SQL"], "javascript": ["JavaScript"], "js": ["JavaScript"], "python": ["Python"],
    "react": ["React"], "html": ["HTML"], "css": ["CSS"], "node": ["Node.js"],
    "express": ["Express"], "flask": ["Flask"], "git": ["Git/GitHub"], "pandas": ["Pandas"],
    "statistics": ["Statistics"], "excel": ["Excel"], "oop": ["OOP"],
    "object oriented": ["OOP"], "rest": ["REST APIs"], "api": ["APIs", "REST APIs"],
}


def skills_for_subject(subject):
    s = (subject or "").lower()
    found = []
    for key, skills in SUBJECT_SKILLS.items():
        if key in s:
            found += [x for x in skills if x not in found]
    for skills in data.ROLE_SKILLS.values():          # exact skill names, e.g. "Responsive Design"
        for sk in skills:
            if sk.lower() in s and sk not in found:
                found.append(sk)
    return found


def subject_performance(user_id):
    """{subject: average percent} over the learner's recent quizzes."""
    buckets = {}
    for subject, pct in quizzes.recent_scores(user_id, limit=10):
        buckets.setdefault(subject, []).append(pct)
    return {s: round(sum(v) / len(v)) for s, v in buckets.items()}


def build(user_id, analysis):
    """The recommendation card: headline, reason, and three actions."""
    perf = subject_performance(user_id)
    gaps = analysis["focus"]
    all_gaps = analysis["missing"] + analysis["partial"]
    strong = sorted(((s, p) for s, p in perf.items() if p >= 75), key=lambda x: -x[1])
    weak = sorted(((s, p) for s, p in perf.items() if p < 60), key=lambda x: x[1])

    priority, reason_bits = None, []
    # 1) A weak quiz subject that maps to one of the learner's gaps wins: fix what is shaky first.
    for subject, pct in weak:
        match = [s for s in skills_for_subject(subject) if s in all_gaps or s in
                 [r["skill"] for r in analysis["rows"] if r["level"] < 100]]
        if match:
            priority = match[0]
            reason_bits.append("You scored %d%% on %s, so %s needs another pass before you move on."
                               % (pct, subject, priority))
            break
    # 2) Otherwise the first remaining gap.
    if not priority and gaps:
        priority = gaps[0]
        n = len(all_gaps)
        reason_bits.append("%s is one of your %d remaining skill gaps for %s."
                           % (priority, n, analysis["role"]) if n > 1 else
                           "%s is your last remaining skill gap for %s." % (priority, analysis["role"]))
    strength = ("Your %s fundamentals are strong (%d%%). " % strong[0]) if strong else ""

    if not priority:
        return {"skill": None, "headline": "You have covered every skill for %s." % analysis["role"],
                "reason": "%sKeep sharpening with practice problems and quizzes on your own study material."
                          % strength,
                "actions": _actions(user_id, None), "strength": strength.strip()}
    return {"skill": priority, "headline": "Focus next: %s" % priority,
            "reason": (strength + " ".join(reason_bits)).strip(), "actions": _actions(user_id, priority),
            "strength": strength.strip()}


def _actions(user_id, skill):
    out = []
    if skill:
        out.append({"label": "Learn %s" % skill, "url": url_for("learning.learn", skill=skill),
                    "primary": True})
        pid = problems.practice_for_skill(user_id, skill)
        out.append({"label": "Practice Problem",
                    "url": url_for("learning.problem", problem_id=pid) if pid else url_for("learning.problem_list")})
        out.append({"label": "Take Quiz", "url": url_for("upload", skill=skill)})
    else:
        out.append({"label": "Practice Problem", "url": url_for("learning.problem_list"), "primary": True})
        out.append({"label": "Take Quiz", "url": url_for("upload")})
    return out


def learner_context(user_id, analysis, profile):
    """Plain-text snapshot of the learner for the assistant's system prompt."""
    rows = gamification.activity_rows(user_id)
    gam = gamification.summary(user_id, rows)
    perf = subject_performance(user_id)
    weak = gamification.weak_topics(user_id, rows)
    problem, solved = problems.today_for(user_id, analysis["role"], analysis["focus"])
    rec = build(user_id, analysis)
    lines = [
        "Learner: %s" % profile["name"],
        "Target role: %s" % analysis["role"],
        "Skill readiness: %d%%" % analysis["readiness"],
        "Skills the role needs, with the learner's level: " +
        ", ".join("%s %d%%" % (r["skill"], r["level"]) for r in analysis["rows"]),
        "Skill gaps (largest first): " + (", ".join(analysis["focus"]) or "none"),
        "Skills the learner says they have: %s" % (profile.get("current_skills") or "not stated"),
        "Recent quiz performance: " + ("; ".join("%s %d%%" % kv for kv in perf.items()) or "no quizzes yet"),
        "Topics missed most in recent quizzes: " + (", ".join("%s (x%d)" % kv for kv in weak[:6]) or "none yet"),
        "Progress: Level %d %s, %d XP, %d-day streak" % (gam["level"], gam["level_name"], gam["xp"], gam["streak"]),
        "Recent activity: " + ("; ".join("%s (%s)" % (a["title"], a["meta"])
                                         for a in gamification.recent_activity(user_id, 5, rows)) or "none"),
        "Today's Problem of the Day: %s (%s, %s)%s" % (
            problem["title"], problem["domain"], problem["difficulty"], " - already solved" if solved else "")
        if problem else "Today's Problem of the Day: none",
        "SkillSphere's current recommendation: %s" % rec["reason"] if rec["reason"] else "",
    ]
    return "\n".join(l for l in lines if l)
