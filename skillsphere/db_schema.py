"""Tables added in the learning-platform upgrade. One definition, two dialects:
MySQL (the real database) and SQLite (in-memory fallback when MySQL is unreachable).
Every statement is CREATE TABLE IF NOT EXISTS, so it is safe to run on an existing
database - no data is dropped.
"""

_TABLES = [
    ("quizzes", """
CREATE TABLE IF NOT EXISTS quizzes (
  id           {PK},
  user_id      INT NOT NULL,
  title        VARCHAR(160),
  subject      VARCHAR(120),
  source       VARCHAR(10) NOT NULL,
  questions    TEXT NOT NULL,
  result       TEXT NULL,
  score        INT NULL,
  total        INT NOT NULL,
  created_at   DATETIME NOT NULL,
  submitted_at DATETIME NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)"""),
    ("problems", """
CREATE TABLE IF NOT EXISTS problems (
  id            {PK},
  title         VARCHAR(120) NOT NULL UNIQUE,
  domain        VARCHAR(40) NOT NULL,
  topic         VARCHAR(60) NOT NULL,
  skill         VARCHAR(60) NULL,
  difficulty    VARCHAR(10) NOT NULL,
  description   TEXT NOT NULL,
  example_input TEXT NULL,
  example_output TEXT NULL,
  constraints_text TEXT NULL,
  hints         TEXT NULL,
  solution      TEXT NULL,
  solution_code TEXT NULL,
  xp_reward     INT NOT NULL DEFAULT 50
)"""),
    ("daily_problems", """
CREATE TABLE IF NOT EXISTS daily_problems (
  id         {PK},
  user_id    INT NOT NULL,
  day        DATE NOT NULL,
  problem_id INT NOT NULL,
  UNIQUE (user_id, day),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
)"""),
    ("problem_solves", """
CREATE TABLE IF NOT EXISTS problem_solves (
  id         {PK},
  user_id    INT NOT NULL,
  problem_id INT NOT NULL,
  xp_awarded INT NOT NULL DEFAULT 0,
  solved_at  DATETIME NOT NULL,
  UNIQUE (user_id, problem_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
)"""),
    ("user_skills", """
CREATE TABLE IF NOT EXISTS user_skills (
  id         {PK},
  user_id    INT NOT NULL,
  skill      VARCHAR(80) NOT NULL,
  level      INT NOT NULL,
  updated_at DATETIME NOT NULL,
  UNIQUE (user_id, skill),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)"""),
    ("learning_activity", """
CREATE TABLE IF NOT EXISTS learning_activity (
  id            {PK},
  user_id       INT NOT NULL,
  activity_type VARCHAR(20) NOT NULL,
  title         VARCHAR(200) NOT NULL,
  ref           VARCHAR(80) NULL,
  xp            INT NOT NULL DEFAULT 0,
  detail        TEXT NULL,
  activity_date DATE NOT NULL,
  created_at    DATETIME NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)"""),
    ("badges", """
CREATE TABLE IF NOT EXISTS badges (
  code        VARCHAR(30) PRIMARY KEY,
  name        VARCHAR(60) NOT NULL,
  description VARCHAR(160) NOT NULL,
  glyph       VARCHAR(6) NOT NULL
)"""),
    ("user_badges", """
CREATE TABLE IF NOT EXISTS user_badges (
  id         {PK},
  user_id    INT NOT NULL,
  badge_code VARCHAR(30) NOT NULL,
  earned_at  DATETIME NOT NULL,
  UNIQUE (user_id, badge_code),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (badge_code) REFERENCES badges(code) ON DELETE CASCADE
)"""),
]

TABLE_NAMES = [name for name, _ in _TABLES]


def ddl(dialect):
    pk = ("INTEGER PRIMARY KEY AUTOINCREMENT" if dialect == "sqlite"
          else "INT AUTO_INCREMENT PRIMARY KEY")
    return [sql.replace("{PK}", pk).strip() for _, sql in _TABLES]
