"""SkillSphere Assistant page and chat API (Flask blueprint)."""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

import assistant
import data
import db
import recommend
import skills

bp = Blueprint("assistant", __name__)


def _context():
    profile = db.get_profile(session.get("user_id"))
    if not profile:
        return None, None, None
    a = data.analyse(profile["target_role"], profile["current_skills"], skills.get_levels(profile["id"]))
    return profile, a, recommend.learner_context(profile["id"], a, profile)


def suggestions(analysis):
    chips = ["What should I learn next?"]
    if analysis["focus"]:
        chips.append("Why is %s showing as my skill gap?" % analysis["focus"][0])
    chips += ["Give me a practice problem", "What should I revise?"]
    return chips


@bp.route("/assistant")
def page():
    profile, a, _ = _context()
    if not profile:
        flash("Create your profile first - it takes about 30 seconds.", "info")
        return redirect(url_for("profile"))
    return render_template("assistant.html", chips=suggestions(a))


@bp.route("/api/assistant", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    profile, a, context = _context()
    if not profile:
        return jsonify({"ok": False, "reply": "Create your profile first so I know your goals."}), 400
    result = assistant.reply(context, payload.get("message"), payload.get("history"))
    return jsonify(result), (200 if result["ok"] else 502)
