"""Problems, Problem of the Day and learning tasks (Flask blueprint)."""
from flask import (Blueprint, flash, redirect, render_template, request, session, url_for)

import data
import db
import gamification
import problems
import skills

bp = Blueprint("learning", __name__)


def _profile():
    return db.get_profile(session.get("user_id"))


def _guard():
    if not _profile():
        flash("Create your profile first - it takes about 30 seconds.", "info")
        return redirect(url_for("profile"))
    return None


def _analysis(profile):
    return data.analyse(profile["target_role"], profile["current_skills"],
                        skills.get_levels(profile["id"]))


@bp.route("/problems")
def problem_list():
    guard = _guard()
    if guard:
        return guard
    uid = session["user_id"]
    domain = request.args.get("domain") or None
    rows = problems.list_all(uid, domain)
    a = _analysis(_profile())
    today, today_solved = problems.today_for(uid, a["role"], a["focus"])
    return render_template("problems.html", rows=rows, domains=problems.domains(), domain=domain,
                           today=today, today_solved=today_solved)


@bp.route("/problem-of-the-day")
def problem_of_the_day():
    guard = _guard()
    if guard:
        return guard
    a = _analysis(_profile())
    today, _ = problems.today_for(session["user_id"], a["role"], a["focus"])
    if not today:
        flash("No problems are available yet.", "info")
        return redirect(url_for("dashboard"))
    return redirect(url_for("learning.problem", problem_id=today["id"]))


@bp.route("/problems/<int:problem_id>")
def problem(problem_id):
    guard = _guard()
    if guard:
        return guard
    uid = session["user_id"]
    p = problems.get(problem_id)
    if not p:
        return render_template("error.html", code=404, message="That problem does not exist."), 404
    return render_template("problem.html", p=p, solved=problem_id in problems.solved_ids(uid),
                           is_daily=problems.is_todays(uid, problem_id))


@bp.route("/problems/<int:problem_id>/solve", methods=["POST"])
def solve(problem_id):
    guard = _guard()
    if guard:
        return guard
    uid = session["user_id"]
    p = problems.get(problem_id)
    if not p:
        return redirect(url_for("learning.problem_list"))
    result = gamification.on_problem_solved(uid, p, problems.is_todays(uid, problem_id))
    if result is None:
        flash("You have already solved this one - no extra XP, but good practice.", "info")
    else:
        for line in gamification.flash_lines(result):
            flash(line, "info")
    return redirect(url_for("learning.problem", problem_id=problem_id))


@bp.route("/learn/<path:skill>")
def learn(skill):
    guard = _guard()
    if guard:
        return guard
    uid = session["user_id"]
    a = _analysis(_profile())
    rec = data.recommendation_for(skill)
    level = next((r["level"] for r in a["rows"] if r["skill"] == skill), 0)
    task_done = bool(db.q_one("SELECT id FROM learning_activity WHERE user_id=%s AND "
                              "activity_type='learning_task' AND ref=%s", (uid, skill)))
    pid = problems.practice_for_skill(uid, skill)
    return render_template("learn.html", skill=skill, rec=rec, level=level, task_done=task_done,
                           practice_id=pid, a=a,
                           focus_items=[f.strip() for f in rec["focus"].split(",")])


@bp.route("/learn/<path:skill>/complete", methods=["POST"])
def learn_complete(skill):
    guard = _guard()
    if guard:
        return guard
    uid = session["user_id"]
    result = gamification.on_learning_task_completed(uid, skill)
    if result is None:
        flash("You already completed the learning task for %s." % skill, "info")
    else:
        skills.set_level(uid, skill, 100)
        for line in gamification.flash_lines(result):
            flash(line, "info")
    return redirect(url_for("learning.learn", skill=skill))
