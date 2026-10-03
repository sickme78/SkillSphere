# SkillSphere AI

**Identify your skill gaps. Learn what matters.**

Mini project for SIH 2026 problem statement **SIH26101** — AI-Enabled Skill Intelligence and
Personalized Learning Platform.

Stack: HTML + CSS + JavaScript · Python Flask · MySQL · Gemini API · pypdf / python-pptx

---

## 1. What it does

Profile → target role → rule-based skill gap analysis → personalised learning path →
upload ANY PDF/PPTX/TXT → full text extraction → (long documents are sampled across all sections) →
Gemini writes questions from that document → quiz → score, explanations and weak topics → dashboard.

On top of that core loop:

- **Problem of the Day** - one daily exercise chosen from your skill gaps / target role (28 starter
  problems across DSA, Python, JavaScript, SQL, DBMS, Web Dev, C++, Java, CS fundamentals, stored in MySQL).
- **XP, levels, badges, streaks** - earned only by real learning actions (quiz, problem, learning task).
- **Personalised dashboard** - role, readiness, gaps, recommendation, POTD, progress, activity, badges.
- **SkillSphere Assistant** - Gemini chat that sees your role, gaps, quiz results and progress.
- **Recommendations** - ties it together: Learn, Practice, Quiz, earn XP, repeat.

The JavaScript demo quiz runs **only** when you press "Run demo quiz". If Gemini fails you get a clear
error - never silently-substituted questions.

### XP rules
Quiz completed +50 · score 80%+ +100 more · Problem of the Day +50 (its XP reward) · practice problem +25 ·
learning task +75 · streak bonus +5 x streak days (max 7) on the first action of a day. Max 5 XP-earning quizzes/day.
Levels: Explorer 0 · Learner 150 · Builder 400 · Achiever 1000 · Skill Master 2000 XP.

---

## 2. Setup on Windows (step by step)

### Step 1 — Install Python
Download Python 3.10 or newer from python.org. **Tick "Add Python to PATH"** during installation.
Check it worked:

    python --version

### Step 2 — Install MySQL
Install MySQL Community Server (and MySQL Workbench, which is easier for beginners).
Remember the root password you set.

### Step 3 — Create the database
Open Command Prompt in the project folder and run:

    mysql -u root -p < schema.sql

Type your MySQL password when asked. This creates the `skillsphere` database, all tables and the
seed data for roles and skills. (In Workbench you can instead open `schema.sql` and click the
lightning bolt.)

If `mysql` is not recognised, use the full path, for example:

    "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p < schema.sql

### Step 4 — Create and activate a virtual environment

    python -m venv venv
    venv\Scripts\activate

Your prompt now starts with `(venv)`.

### Step 5 — Install the dependencies

    pip install -r requirements.txt

### Step 6 — Configure `.env`
Copy `.env.example` to `.env`:

    copy .env.example .env

Open `.env` in Notepad and set your MySQL password (and your Gemini key if you have one):

    GEMINI_API_KEY=your_key_here
    DB_HOST=localhost
    DB_PORT=3306
    DB_USER=root
    DB_PASSWORD=your_mysql_password
    DB_NAME=skillsphere
    SECRET_KEY=change-this-for-your-demo

`.env` is never committed and the key is only ever read in Python, never in the browser.

### Step 7 — Run the app

    python app.py

### Step 8 — Open the browser

    http://127.0.0.1:5000

To stop the server press `Ctrl + C`. Next time you work on the project, activate the virtual
environment again with `venv\Scripts\activate` before `python app.py`.

---

## 3. Configuring the Gemini API

1. Go to Google AI Studio and create an API key.
2. Paste it into `.env` as `GEMINI_API_KEY=AIza...`
3. Restart Flask (`Ctrl + C`, then `python app.py`).

The app calls `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`
from `ai.py`, asks for strict JSON, and validates every question before showing the quiz.
To use a different model, set `GEMINI_MODEL` in `.env`.

---

## 4. Demo mode (so the presentation never fails)

Demo mode runs automatically when:

- no Gemini key is configured,
- the Gemini call fails (no internet, quota, timeout), or
- the model returns something that is not valid quiz JSON.

It can also be triggered on purpose with the **"Run demo quiz instead"** button on the AI Quiz page.
It uses 5 prepared questions about JavaScript fundamentals, defined as `DEMO_QUESTIONS` in `ai.py`.
The quiz page always states whether the questions came from Gemini or from demo mode.

The same safety net exists for MySQL: if the database is unreachable, the app stores data in memory
for that session and shows a note in the sidebar instead of crashing.

---

## 5. Sample material for the demo

`sample/JavaScript_Fundamentals.pdf` is ready to upload. The plain text version is in
`sample/javascript_fundamentals.txt` if you want to edit it and re-export.

---

## 6. Presentation demo sequence (3–5 minutes)

1. Open `http://127.0.0.1:5000` — landing page with the live skill map visual.
2. Click **Build my skill profile**.
3. Fill in: Radhika · Frontend Developer · current skills `HTML, CSS, Basic JavaScript` ·
   goal "Become job-ready as a frontend developer".
   *(Or click "Explore demo" on the landing page to skip typing.)*
4. Submit → **Skill gap analysis**: readiness counts up, bars animate, next focus is listed.
5. Click **See my learning path** → personalised recommendations with difficulty and focus areas.
6. Click **Turn my material into a quiz** → AI Quiz Generator.
7. Upload `sample/JavaScript_Fundamentals.pdf` → **Generate quiz**.
8. Answer the 5 questions using Next / Previous, then **Submit quiz**.
9. **Results**: score, verdict, what you know / what to revisit, per-question explanations.
10. Click **See my dashboard** → readiness, stats, next best action, quiz history.

Fallback if the wifi dies mid-demo: press **Run demo quiz instead** on step 7.

---

## 7. What is real and what is an MVP placeholder

**Fully functional**
- Profile creation and storage in MySQL
- Rule-based skill gap analysis and readiness percentage
- Learning recommendations derived from the detected gaps
- PDF and PPTX upload with real text extraction
- Gemini API call, strict-JSON parsing and validation
- Quiz interface, scoring, explanations, topic breakdown
- Quiz results stored in MySQL and shown on the dashboard
- Error handling for missing key, bad file, API failure, DB failure

**MVP placeholders (say this honestly in the viva)**
- Skill requirements per role are a curated dataset in `data.py`, not scraped job-market data
- The readiness score is a rule-based comparison, labelled "Initial Skill Gap Analysis" — it is
  not an AI competency model
- Learning recommendations are a curated dataset, not live course links
- Login is a demo profile; there is no password authentication
- Quiz results do not yet feed back into the readiness score (planned next step)

---

## 8. Project structure

    skillsphere/
    ├── app.py              Flask routes
    ├── data.py             Role -> required skills, recommendations, gap analysis
    ├── db.py               MySQL access + in-memory fallback
    ├── ai.py               Gemini call, JSON validation, demo questions
    ├── extract.py          PDF / PPTX text extraction
    ├── schema.sql          Database schema + seed data
    ├── requirements.txt
    ├── .env.example
    ├── templates/          index, profile, skill_gap, recommendations, upload,
    │                       quiz, results, dashboard, base, error
    ├── static/css/style.css
    ├── static/js/script.js
    ├── sample/             JavaScript_Fundamentals.pdf + .txt
    └── uploads/            Files uploaded during the demo

---

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| `venv\Scripts\activate` blocked | Run `Set-ExecutionPolicy -Scope Process RemoteSigned` in PowerShell, or use Command Prompt |
| "MySQL is not reachable" in terminal | Check the MySQL service is running and that `DB_PASSWORD` in `.env` is correct |
| Quiz always says demo mode | `GEMINI_API_KEY` missing or invalid in `.env`; restart Flask after editing |
| "Not enough readable text" | The PDF is a scanned image; use the sample PDF |
| Port 5000 busy | Change the port in the last line of `app.py` |
