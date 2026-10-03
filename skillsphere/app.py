"""SkillSphere AI - Flask MVP. Run with: python app.py"""
import os
from datetime import datetime

from dotenv import load_dotenv
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)
from werkzeug.utils import secure_filename

import ai
import bp_assistant
import bp_learning
import data
import db
import extract
import gamification
import material
import problems
import quizzes
import recommend
import skills

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "skillsphere-dev-secret")

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".ppt", ".txt"}
MAX_UPLOAD_MB = 10
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
app.register_blueprint(bp_learning.bp)
app.register_blueprint(bp_assistant.bp)

DEMO_PROFILE = {
    "name": "Radhika",
    "email": "radhika@example.com",
    "education": "B.Tech CSE, 2nd Year",
    "experience": "Fresher - 2 college projects",
    "current_skills": "HTML, CSS",
    "learning_goal": "Become job-ready as a frontend developer.",
    "target_role": "Frontend Developer",
}


# ---------------------------------------------------------------- helpers
@app.context_processor
def inject_globals():
    profile = current_profile()
    gam = gamification.summary(profile["id"]) if profile else None
    return {
        "profile": profile,
        "gam": gam,
        "storage_mode": "MySQL" if session.get("mysql_ok") else "in-memory",
        "mysql_ok": session.get("mysql_ok", True),
        "year": datetime.now().year,
    }


def current_profile():
    return db.get_profile(session.get("user_id"))


def require_profile():
    """Pages after the profile step need a profile; send the user back if missing."""
    if not current_profile():
        flash("Create your profile first - it takes about 30 seconds.", "info")
        return redirect(url_for("profile"))
    return None


def current_analysis():
    p = current_profile()
    if not p:
        return None
    return data.analyse(p["target_role"], p["current_skills"], skills.get_levels(p["id"]))


def greeting():
    hour = datetime.now().hour
    return "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"


# ---------------------------------------------------------------- routes
@app.route("/")
def index():
    preview = data.analyse("Frontend Developer", "HTML, CSS, Basic JavaScript")
    return render_template("index.html", preview=preview)


@app.route("/demo")
def demo_login():
    """One-click demo user so the presentation can start instantly."""
    user_id = db.save_profile(DEMO_PROFILE)
    session["mysql_ok"] = db.using_mysql()
    if not user_id:
        flash("Could not save the demo profile. Check your database settings.", "error")
        return redirect(url_for("profile"))
    session["user_id"] = user_id
    return redirect(url_for("skill_gap"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in
                ("name", "email", "education", "experience", "current_skills",
                 "learning_goal", "target_role")}
        if not form["name"] or not form["email"] or not form["target_role"]:
            flash("Name, email and target role are required.", "error")
            return render_template("profile.html", roles=data.ROLE_SKILLS, form=form)
        user_id = db.save_profile(form)
        session["mysql_ok"] = db.using_mysql()
        if not user_id:
            flash("Your profile could not be saved. Check the database connection.", "error")
            return render_template("profile.html", roles=data.ROLE_SKILLS, form=form)
        session["user_id"] = user_id
        return redirect(url_for("skill_gap"))
    existing = current_profile() or {}
    return render_template("profile.html", roles=data.ROLE_SKILLS, form=existing)


@app.route("/skill-gap")
def skill_gap():
    guard = require_profile()
    if guard:
        return guard
    return render_template("skill_gap.html", a=current_analysis())


@app.route("/recommendations")
def recommendations():
    guard = require_profile()
    if guard:
        return guard
    return render_template("recommendations.html", a=current_analysis())


@app.route("/upload", methods=["GET", "POST"])
def upload():
    guard = require_profile()
    if guard:
        return guard

    if request.method == "POST":
        use_demo = request.form.get("demo") == "1"
        uid = session["user_id"]

        if use_demo:
            result = ai.generate_quiz("", force_demo=True)
            title = "Demo quiz - JavaScript Fundamentals"
        else:
            file = request.files.get("material")
            if not file or not file.filename:
                flash("Choose a PDF, PPTX or TXT file first.", "error")
                return redirect(url_for("upload"))
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                flash("Only PDF, PPTX and TXT files are supported.", "error")
                return redirect(url_for("upload"))
            stored = "%s_%s" % (datetime.now().strftime("%Y%m%d%H%M%S"), secure_filename(file.filename))
            path = os.path.join(UPLOAD_DIR, stored)
            file.save(path)
            try:
                text = extract.extract_text(path)
                prepared = material.prepare(text)
            except (extract.ExtractError, material.MaterialError) as exc:
                flash(str(exc), "error")
                return redirect(url_for("upload"))
            except Exception as exc:
                flash("That file could not be read (%s). Try another file." % str(exc)[:100], "error")
                return redirect(url_for("upload"))
            title = os.path.splitext(file.filename)[0][:60]
            result = ai.generate_quiz(prepared["material"], n_questions=prepared["n_questions"],
                                      spread=prepared["sampled"] or prepared["chunks_total"] > 1)
            if result["ok"] and prepared["sampled"]:
                result["message"] += (" Your document is long, so questions were drawn from %d "
                                      "sections spread across it." % prepared["chunks_used"])

        if not result["ok"]:
            # No silent fallback: tell the learner what went wrong and let them choose.
            flash(result["message"] + " Nothing was substituted - you can retry, or run the "
                  "demo quiz on purpose.", "error")
            return redirect(url_for("upload"))

        quiz_id = quizzes.create(uid, title, result["subject"], result["source"], result["questions"])
        if not quiz_id:
            flash("The quiz was generated but could not be saved. Check the database connection.", "error")
            return redirect(url_for("upload"))
        session["quiz_id"] = quiz_id
        flash(result["message"], "info" if result["source"] == "gemini" else "warn")
        return redirect(url_for("quiz"))

    return render_template("upload.html", key_ready=ai.key_configured(),
                           skill=request.args.get("skill"))


@app.route("/generate-quiz", methods=["POST"])
def generate_quiz_api():
    """JSON API: {"text": "..."} -> {"source", "subject", "message", "questions": [...]}"""
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Send a 'text' field with the study material."}), 400
    try:
        prepared = material.prepare(extract.clean(text))
    except material.MaterialError as exc:
        return jsonify({"error": str(exc)}), 400
    result = ai.generate_quiz(prepared["material"], n_questions=prepared["n_questions"],
                              spread=prepared["chunks_total"] > 1)
    status = 200 if result["ok"] else 502
    return jsonify({"source": result["source"], "subject": result["subject"],
                    "message": result["message"], "questions": result["questions"]}), status


@app.route("/quiz")
def quiz():
    guard = require_profile()
    if guard:
        return guard
    q = quizzes.get(session.get("quiz_id"), session["user_id"])
    if not q:
        flash("Generate a quiz first.", "info")
        return redirect(url_for("upload"))
    if q["submitted_at"]:
        return redirect(url_for("results"))
    return render_template("quiz.html", questions=q["questions"], title=q["title"],
                           subject=q["subject"], source=q["source"])


@app.route("/submit-quiz", methods=["POST"])
def submit_quiz():
    guard = require_profile()
    if guard:
        return guard
    uid = session["user_id"]
    q = quizzes.get(session.get("quiz_id"), uid)
    if not q:
        return redirect(url_for("upload"))
    if q["submitted_at"]:                       # already graded: never award XP twice
        return redirect(url_for("results"))

    review, score = [], 0
    for i, item in enumerate(q["questions"]):
        chosen = request.form.get("q%d" % i)
        correct = chosen == item["answer"]
        score += 1 if correct else 0
        review.append({
            "question": item["question"],
            "options": item["options"],
            "user_answer": chosen or "-",
            "correct_answer": item["answer"],
            "is_correct": correct,
            "explanation": item.get("explanation", ""),
            "topic": item.get("topic", "General"),
        })

    total = len(q["questions"])
    db.save_quiz_result(uid, q["title"], score, total, review)
    quizzes.save_result(q["id"], score, review)
    weak = sorted({r["topic"] for r in review if not r["is_correct"]})
    strong = sorted({r["topic"] for r in review if r["is_correct"]} - set(weak))
    events = gamification.on_quiz_completed(uid, q["title"], q["subject"], score, total, weak, strong, q["id"])
    for line in gamification.flash_lines(events):
        flash(line, "info")
    session["last_quiz_id"] = q["id"]
    return redirect(url_for("results"))


@app.route("/results")
def results():
    guard = require_profile()
    if guard:
        return guard
    q = quizzes.get(session.get("last_quiz_id") or session.get("quiz_id"), session["user_id"])
    if not q or not q["submitted_at"]:
        flash("No quiz has been submitted yet.", "info")
        return redirect(url_for("upload"))
    result = {"title": q["title"], "score": q["score"], "total": q["total"], "review": q["result"]}
    percent = round(result["score"] * 100 / result["total"]) if result["total"] else 0
    verdict = ("Strong understanding of the fundamentals." if percent >= 80 else
               "Solid start - a few concepts need another pass." if percent >= 50 else
               "Worth revisiting this material before moving on.")
    known = sorted({r["topic"] for r in result["review"] if r["is_correct"]})
    revisit = sorted({r["topic"] for r in result["review"] if not r["is_correct"]})
    a = current_analysis()
    related = recommend.skills_for_subject(q["subject"] or q["title"])
    return render_template("results.html", r=result, percent=percent, verdict=verdict,
                           known=known, revisit=revisit, subject=q["subject"], related=related,
                           rec=recommend.build(session["user_id"], a))


@app.route("/dashboard")
def dashboard():
    guard = require_profile()
    if guard:
        return guard
    uid = session["user_id"]
    a = current_analysis()
    rows = gamification.activity_rows(uid)
    history = db.get_quiz_results(uid)
    avg = round(sum(h["score"] * 100 / h["total"] for h in history) / len(history)) if history else None
    problem, problem_solved = problems.today_for(uid, a["role"], a["focus"])
    return render_template(
        "dashboard.html", a=a, history=history, avg=avg, greeting=greeting(),
        gam=gamification.summary(uid, rows),
        feed=gamification.recent_activity(uid, 6, rows),
        quiz_count=sum(1 for r in rows if r["activity_type"] == "quiz"),
        recent_scores=quizzes.recent_scores(uid, 5),
        weak=gamification.weak_topics(uid, rows)[:4],
        badges=gamification.all_badges(uid),
        problem=problem, problem_solved=problem_solved,
        rec=recommend.build(uid, a))


@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------------------------------------------- errors
@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404,
                           message="That page does not exist."), 404


@app.errorhandler(413)
def too_large(_):
    return render_template("error.html", code=413,
                           message="That file is larger than %d MB." % MAX_UPLOAD_MB), 413


@app.errorhandler(500)
def server_error(_):
    return render_template("error.html", code=500,
                           message="Something went wrong on the server. Check the terminal "
                                   "running Flask for details."), 500


if __name__ == "__main__":
    if not db.using_mysql():
        print("\n[SkillSphere] MySQL is not reachable (%s)." % db.LAST_ERROR)
        print("[SkillSphere] Running with an in-memory store so the demo still works.\n")
    if not ai.key_configured():
        print("[SkillSphere] No GEMINI_API_KEY found - AI quizzes and the assistant are disabled; "
              "the demo quiz still works.\n")
    app.run(debug=True, port=5000)
