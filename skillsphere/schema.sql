-- SkillSphere AI - MySQL schema + seed data
-- Run once:  mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS skillsphere
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE skillsphere;

DROP TABLE IF EXISTS user_badges;
DROP TABLE IF EXISTS badges;
DROP TABLE IF EXISTS learning_activity;
DROP TABLE IF EXISTS user_skills;
DROP TABLE IF EXISTS problem_solves;
DROP TABLE IF EXISTS daily_problems;
DROP TABLE IF EXISTS problems;
DROP TABLE IF EXISTS quizzes;
DROP TABLE IF EXISTS quiz_answers;
DROP TABLE IF EXISTS quiz_results;
DROP TABLE IF EXISTS role_skills;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS profiles;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id    INT AUTO_INCREMENT PRIMARY KEY,
  name  VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE profiles (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  user_id        INT NOT NULL UNIQUE,
  education      VARCHAR(200),
  experience     VARCHAR(200),
  current_skills TEXT,
  learning_goal  TEXT,
  target_role    VARCHAR(80),
  updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Reference data. The Flask app reads roles from data.py for speed,
-- but these tables show the same model in the database.
CREATE TABLE skills (
  id   INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE role_skills (
  id       INT AUTO_INCREMENT PRIMARY KEY,
  role     VARCHAR(80) NOT NULL,
  skill_id INT NOT NULL,
  FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

CREATE TABLE quiz_results (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  quiz_title VARCHAR(160),
  score      INT NOT NULL,
  total      INT NOT NULL,
  taken_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE quiz_answers (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  result_id      INT NOT NULL,
  question       VARCHAR(500),
  user_answer    VARCHAR(4),
  correct_answer VARCHAR(4),
  is_correct     TINYINT(1),
  FOREIGN KEY (result_id) REFERENCES quiz_results(id) ON DELETE CASCADE
);

-- ---------- seed data ----------
INSERT INTO skills (name) VALUES
('HTML'),('CSS'),('JavaScript'),('Git/GitHub'),('React'),('Responsive Design'),('APIs'),
('Python'),('Flask'),('SQL'),('REST APIs'),('Authentication'),('Database Design'),
('Node.js'),('Express'),('OOP'),('Excel'),('Pandas'),('Data Visualization'),('Statistics');

INSERT INTO role_skills (role, skill_id)
SELECT 'Frontend Developer', id FROM skills
WHERE name IN ('HTML','CSS','JavaScript','Git/GitHub','React','Responsive Design','APIs');

INSERT INTO role_skills (role, skill_id)
SELECT 'Backend Developer', id FROM skills
WHERE name IN ('Python','Flask','SQL','REST APIs','Git/GitHub','Authentication','Database Design');

INSERT INTO role_skills (role, skill_id)
SELECT 'Full Stack Developer', id FROM skills
WHERE name IN ('HTML','CSS','JavaScript','React','Node.js','Express','SQL','Git/GitHub','REST APIs');

INSERT INTO role_skills (role, skill_id)
SELECT 'Data Analyst', id FROM skills
WHERE name IN ('Python','SQL','Excel','Pandas','Data Visualization','Statistics');

INSERT INTO role_skills (role, skill_id)
SELECT 'Python Developer', id FROM skills
WHERE name IN ('Python','OOP','SQL','Flask','APIs','Git/GitHub');

-- ---------- learning-platform tables (quizzes, problems, XP/activity, badges) ----------
-- NOTE: the Flask app also creates these automatically on startup (CREATE TABLE IF NOT EXISTS),
-- so an existing database upgrades itself without losing data. Badges and the 28 starter
-- problems are seeded by the app on first run.

CREATE TABLE IF NOT EXISTS quizzes (
  id           INT AUTO_INCREMENT PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS problems (
  id            INT AUTO_INCREMENT PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS daily_problems (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  day        DATE NOT NULL,
  problem_id INT NOT NULL,
  UNIQUE (user_id, day),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS problem_solves (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  problem_id INT NOT NULL,
  xp_awarded INT NOT NULL DEFAULT 0,
  solved_at  DATETIME NOT NULL,
  UNIQUE (user_id, problem_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_skills (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  skill      VARCHAR(80) NOT NULL,
  level      INT NOT NULL,
  updated_at DATETIME NOT NULL,
  UNIQUE (user_id, skill),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS learning_activity (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  user_id       INT NOT NULL,
  activity_type VARCHAR(20) NOT NULL,
  title         VARCHAR(200) NOT NULL,
  ref           VARCHAR(80) NULL,
  xp            INT NOT NULL DEFAULT 0,
  detail        TEXT NULL,
  activity_date DATE NOT NULL,
  created_at    DATETIME NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS badges (
  code        VARCHAR(30) PRIMARY KEY,
  name        VARCHAR(60) NOT NULL,
  description VARCHAR(160) NOT NULL,
  glyph       VARCHAR(6) NOT NULL
);

CREATE TABLE IF NOT EXISTS user_badges (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  badge_code VARCHAR(30) NOT NULL,
  earned_at  DATETIME NOT NULL,
  UNIQUE (user_id, badge_code),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (badge_code) REFERENCES badges(code) ON DELETE CASCADE
);
