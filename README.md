# SkillSphere AI 🎯

**An AI-assisted personalized learning and skill development platform.**

SkillSphere AI helps learners identify skill gaps for their target career roles, explore learning resources, practise coding problems, and generate quizzes from study materials.

🌐 **Live Demo:** [SkillSphere AI](https://skillsphere-eymt.onrender.com)

## ✨ Features

- **Skill Gap Analysis:** Identify missing skills based on curated role requirements.
- **Personalized Learning:** Get recommendations for skills to focus on next.
- **AI Quiz:** Generate quiz questions from learning materials.
- **Coding Practice:** Practise problems related to your target role.
- **Progress Dashboard:** View skill readiness, experience points (XP), and streaks.
- **Learning Assistant:** Access learning support through the application.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| Flask | Web application framework |
| HTML, CSS, JavaScript | Frontend |
| MySQL | Intended database |
| Google Gemini API | AI-assisted quiz generation |
| Render | Deployment |

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/sickme78/SkillSphere.git
cd SkillSphere/skillsphere
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file and configure the environment variables required by the application. Use the variable names expected by the project code.

**Security:** Never commit your `.env` file, API keys, database passwords, or other secrets to GitHub.

### 5. Start the application

Follow the startup instructions supported by the Flask application.

## 🔮 Future Improvements

- Reliable persistent database storage
- Improved account and progress persistence
- More personalized learning recommendations
- Expanded role requirements and coding problems
- Enhanced progress analytics

## 📌 Project Status

SkillSphere AI is a student project currently under development. Database connectivity and persistent user progress are areas for further testing and improvement.

## 👩‍💻 Author

**Radhika Jha**

[GitHub Profile](https://github.com/sickme78)
