"""
Static MVP datasets: role -> required skills, and skill -> learning recommendation.
This is rule-based on purpose (see README) and is NOT an AI competency model.
"""

ROLE_SKILLS = {
    "Frontend Developer": ["HTML", "CSS", "JavaScript", "Git/GitHub", "React", "Responsive Design", "APIs"],
    "Backend Developer": ["Python", "Flask", "SQL", "REST APIs", "Git/GitHub", "Authentication", "Database Design"],
    "Full Stack Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js", "Express", "SQL", "Git/GitHub", "REST APIs"],
    "Data Analyst": ["Python", "SQL", "Excel", "Pandas", "Data Visualization", "Statistics"],
    "Python Developer": ["Python", "OOP", "SQL", "Flask", "APIs", "Git/GitHub"],
}

# skill -> (difficulty, focus areas, one-line description)
RECOMMENDATIONS = {
    "HTML": ("Beginner", "Semantic tags, forms, accessibility", "Structure pages the way browsers and screen readers expect."),
    "CSS": ("Beginner", "Flexbox, Grid, custom properties", "Lay out real interfaces instead of fighting the browser."),
    "JavaScript": ("Beginner", "ES6, DOM, functions, events", "The language that turns a static page into a product."),
    "Git/GitHub": ("Beginner", "Repositories, commits, branches, pull requests", "Every team expects this on day one."),
    "React": ("Intermediate", "Components, props, state, hooks", "Build interfaces out of reusable pieces."),
    "Responsive Design": ("Beginner", "Media queries, fluid type, mobile-first", "One layout that holds up from phone to desktop."),
    "APIs": ("Intermediate", "fetch, JSON, async/await, error states", "Connect your interface to real data."),
    "REST APIs": ("Intermediate", "Resources, verbs, status codes, JSON", "Design endpoints other developers can guess correctly."),
    "Python": ("Beginner", "Data types, functions, modules, virtual envs", "The base language for your backend and analysis work."),
    "Flask": ("Intermediate", "Routing, templates, sessions, blueprints", "A small framework you can fully understand."),
    "SQL": ("Beginner", "SELECT, JOIN, GROUP BY, indexes", "Ask a database precise questions."),
    "Authentication": ("Intermediate", "Sessions, password hashing, access control", "Keep user accounts safe by default."),
    "Database Design": ("Intermediate", "Normalisation, keys, relationships", "Model data once so queries stay simple."),
    "Node.js": ("Intermediate", "Modules, npm, async I/O", "Run JavaScript on the server."),
    "Express": ("Intermediate", "Middleware, routing, error handling", "Minimal server framework for Node."),
    "OOP": ("Beginner", "Classes, inheritance, encapsulation", "Organise code around the things it represents."),
    "Excel": ("Beginner", "Formulas, pivot tables, lookup functions", "Still the fastest tool for small analysis."),
    "Pandas": ("Intermediate", "DataFrames, cleaning, groupby, merge", "Handle tabular data in a few lines."),
    "Data Visualization": ("Intermediate", "Charts, matplotlib, chart choice", "Show a finding so people act on it."),
    "Statistics": ("Intermediate", "Distributions, correlation, significance", "Know when a number actually means something."),
}


def recommendation_for(skill):
    difficulty, focus, desc = RECOMMENDATIONS.get(
        skill, ("Beginner", "Core concepts and practice projects", "Build a small project using this skill.")
    )
    return {"skill": skill, "difficulty": difficulty, "focus": focus, "description": desc}


def parse_skills(raw):
    """'HTML, CSS, Basic JavaScript' -> {'HTML':100,'CSS':100,'JavaScript':60}"""
    levels = {}
    for chunk in (raw or "").replace("\n", ",").split(","):
        token = chunk.strip()
        if not token:
            continue
        level = 100
        low = token.lower()
        for word, value in (("basic ", 60), ("beginner ", 60), ("learning ", 40),
                            ("intermediate ", 75), ("some ", 50), ("advanced ", 100)):
            if low.startswith(word):
                level = value
                token = token[len(word):].strip()
                break
        levels[token.lower()] = level
    return levels


ALIASES = {
    "js": "javascript", "javascript (es6)": "javascript", "git": "git/github",
    "github": "git/github", "reactjs": "react", "react.js": "react",
    "node": "node.js", "nodejs": "node.js", "rest api": "rest apis",
    "api": "apis", "restapi": "rest apis", "mysql": "sql", "postgres": "sql",
    "html5": "html", "css3": "css", "responsive": "responsive design",
    "object oriented programming": "oop", "pandas library": "pandas",
}


def analyse(role, raw_skills, earned=None):
    """Rule-based skill gap analysis. Returns a dict used by every page.

    `earned` is an optional {skill name: level} dict of progress made inside SkillSphere
    (see skills.py); it is merged over the profile text, higher value wins."""
    required = ROLE_SKILLS.get(role, [])
    have = parse_skills(raw_skills)
    have = {ALIASES.get(k, k): v for k, v in have.items()}
    for skill_name, lvl in (earned or {}).items():
        key = skill_name.lower()
        have[key] = max(have.get(key, 0), lvl)

    rows, matched, partial, missing = [], [], [], []
    for skill in required:
        level = have.get(skill.lower(), 0)
        # 'git/github' also matches a plain 'git' entry, etc.
        if level == 0:
            for key, value in have.items():
                if key and (key in skill.lower() or skill.lower().split("/")[0] == key):
                    level = value
                    break
        rows.append({"skill": skill, "level": level})
        if level >= 100:
            matched.append(skill)
        elif level > 0:
            partial.append(skill)
        else:
            missing.append(skill)

    readiness = round(sum(r["level"] for r in rows) / len(rows)) if rows else 0
    focus = [s for s in missing] + [s for s in partial]
    return {
        "role": role,
        "rows": rows,
        "matched": matched,
        "partial": partial,
        "missing": missing,
        "readiness": readiness,
        "focus": focus[:3],
        "recommendations": [recommendation_for(s) for s in (partial + missing)][:6],
    }
