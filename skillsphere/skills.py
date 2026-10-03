"""Per-learner skill levels earned through SkillSphere (the user_skills table).

The rule-based analysis in data.py starts from what the learner typed in their profile;
levels stored here are merged on top (the higher value wins), so completing a learning
task actually moves the readiness number.
"""
import db


def get_levels(user_id):
    if not user_id:
        return {}
    rows = db.q_all("SELECT skill, level FROM user_skills WHERE user_id=%s", (user_id,))
    return {r["skill"]: int(r["level"]) for r in rows}


def set_level(user_id, skill, level):
    existing = db.q_one("SELECT level FROM user_skills WHERE user_id=%s AND skill=%s", (user_id, skill))
    if existing:
        if int(existing["level"]) >= level:
            return
        db.q_exec("UPDATE user_skills SET level=%s, updated_at=%s WHERE user_id=%s AND skill=%s",
                  (level, db.now_str(), user_id, skill))
    else:
        db.q_exec("INSERT INTO user_skills (user_id, skill, level, updated_at) VALUES (%s,%s,%s,%s)",
                  (user_id, skill, level, db.now_str()))
