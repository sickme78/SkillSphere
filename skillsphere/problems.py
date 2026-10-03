"""Problem of the Day: storage, daily selection and lookups.

Selection is influenced by the learner (see pick_for_today): problems tied to a current
skill gap come first, then problems in the domains usually needed for their target role.
The choice is stored per user per day, so it does not change if they refresh.
"""
import hashlib
from datetime import date

import db
import problem_bank

# Domains that matter for each target role (used when no skill-gap problem is available).
ROLE_DOMAINS = {
    "Frontend Developer": ["JavaScript", "Web Development", "DSA"],
    "Backend Developer": ["Python", "SQL", "DBMS", "DSA"],
    "Full Stack Developer": ["JavaScript", "Web Development", "SQL", "DSA"],
    "Data Analyst": ["SQL", "Python", "CS Fundamentals"],
    "Python Developer": ["Python", "DSA", "SQL"],
}

# Skill -> domains to fall back on when no problem is tagged with that exact skill.
SKILL_DOMAINS = {
    "HTML": ["Web Development"], "CSS": ["Web Development"], "Responsive Design": ["Web Development"],
    "APIs": ["Web Development", "JavaScript"], "REST APIs": ["Web Development", "Python"],
    "JavaScript": ["JavaScript"], "React": ["JavaScript"], "Node.js": ["JavaScript"],
    "Express": ["JavaScript"], "Python": ["Python"], "Flask": ["Python"], "OOP": ["Python", "Java"],
    "Pandas": ["Python"], "SQL": ["SQL", "DBMS"], "Database Design": ["DBMS", "SQL"],
    "Authentication": ["Python", "Web Development"], "Git/GitHub": ["CS Fundamentals"],
    "Excel": ["CS Fundamentals"], "Statistics": ["CS Fundamentals"],
    "Data Visualization": ["Python"],
}

DIFFICULTY_ORDER = {"Easy": 0, "Medium": 1, "Hard": 2}


def seed(run):
    existing = {r["title"] for r in run("SELECT title FROM problems")}
    for p in problem_bank.PROBLEMS:
        if p["title"] in existing:
            continue
        run("INSERT INTO problems (title, domain, topic, skill, difficulty, description, "
            "example_input, example_output, constraints_text, hints, solution, solution_code, "
            "xp_reward) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (p["title"], p["domain"], p["topic"], p["skill"], p["difficulty"], p["description"],
             p["example_input"], p["example_output"], p["constraints"], "\n".join(p["hints"]),
             p["solution"], p["code"], p["xp"]))


def _shape(row):
    if not row:
        return None
    row = dict(row)
    row["hints"] = [h for h in (row.get("hints") or "").split("\n") if h.strip()]
    row["constraints"] = row.get("constraints_text") or ""
    return row


def get(problem_id):
    return _shape(db.q_one("SELECT * FROM problems WHERE id=%s", (problem_id,)))


def list_all(user_id, domain=None):
    solved = solved_ids(user_id)
    rows = db.q_all("SELECT id, title, domain, topic, difficulty, xp_reward FROM problems ORDER BY id")
    rows = [r for r in rows if not domain or r["domain"] == domain]
    rows.sort(key=lambda r: (r["domain"], DIFFICULTY_ORDER.get(r["difficulty"], 9), r["id"]))
    for r in rows:
        r["solved"] = r["id"] in solved
    return rows


def domains():
    return [r["domain"] for r in db.q_all("SELECT DISTINCT domain FROM problems ORDER BY domain")]


def solved_ids(user_id):
    return {r["problem_id"] for r in
            db.q_all("SELECT problem_id FROM problem_solves WHERE user_id=%s", (user_id,))}


def solved_count(user_id):
    return len(solved_ids(user_id))


def _pick(candidates, user_id, key):
    """Deterministic 'random' choice: stable for the same user and key, varies by day."""
    digest = hashlib.sha256(("%s|%s" % (user_id, key)).encode()).hexdigest()
    return candidates[int(digest, 16) % len(candidates)]


def pick_for_today(user_id, role, gaps):
    """Choose a problem: gap-related first, then role-related, then anything unsolved."""
    solved = solved_ids(user_id)
    all_rows = db.q_all("SELECT id, domain, skill, difficulty FROM problems")
    unsolved = [r for r in all_rows if r["id"] not in solved] or all_rows
    if not unsolved:
        return None
    # Early on, keep things approachable.
    n = len(solved)
    allowed = {"Easy"} if n < 3 else {"Easy", "Medium"} if n < 8 else {"Easy", "Medium", "Hard"}
    leveled = [r for r in unsolved if r["difficulty"] in allowed] or unsolved

    gap_skills = set(gaps or [])
    gap_domains = {d for g in gap_skills for d in SKILL_DOMAINS.get(g, [])}
    tiers = [
        [r for r in leveled if r["skill"] in gap_skills],
        [r for r in leveled if r["domain"] in gap_domains],
        [r for r in leveled if r["domain"] in ROLE_DOMAINS.get(role, [])],
        leveled,
    ]
    for tier in tiers:
        if tier:
            return _pick(tier, user_id, date.today().isoformat())["id"]
    return None


def today_for(user_id, role, gaps):
    """Returns (problem, solved_bool). The pick is stored so refreshing never changes it."""
    today = date.today().isoformat()
    row = db.q_one("SELECT problem_id FROM daily_problems WHERE user_id=%s AND day=%s", (user_id, today))
    if row:
        pid = row["problem_id"]
    else:
        pid = pick_for_today(user_id, role, gaps)
        if pid is None:
            return None, False
        db.q_exec("INSERT INTO daily_problems (user_id, day, problem_id) VALUES (%s,%s,%s)",
                  (user_id, today, pid))
    problem = get(pid)
    return problem, pid in solved_ids(user_id)


def is_todays(user_id, problem_id):
    row = db.q_one("SELECT problem_id FROM daily_problems WHERE user_id=%s AND day=%s",
                   (user_id, date.today().isoformat()))
    return bool(row and row["problem_id"] == problem_id)


def practice_for_skill(user_id, skill):
    """An unsolved problem for a skill: exact skill tag first, then the skill's domains."""
    solved = solved_ids(user_id)
    rows = db.q_all("SELECT id, domain, skill, difficulty FROM problems ORDER BY id")
    rows = [r for r in rows if r["id"] not in solved]
    rows.sort(key=lambda r: DIFFICULTY_ORDER.get(r["difficulty"], 9))
    for r in rows:
        if r["skill"] == skill:
            return r["id"]
    for r in rows:
        if r["domain"] in SKILL_DOMAINS.get(skill, []):
            return r["id"]
    return None


def practice_for_domain_text(user_id, text):
    """Used by the assistant: find an unsolved problem whose topic/domain/title matches `text`."""
    text = (text or "").lower()
    solved = solved_ids(user_id)
    rows = db.q_all("SELECT id, title, domain, topic, skill, difficulty FROM problems ORDER BY id")
    rows.sort(key=lambda r: DIFFICULTY_ORDER.get(r["difficulty"], 9))
    for r in rows:
        hay = " ".join(str(r.get(k) or "") for k in ("title", "domain", "topic", "skill")).lower()
        if r["id"] not in solved and any(w in hay for w in text.split() if len(w) > 3):
            return r
    return None
