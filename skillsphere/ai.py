"""
Gemini access for SkillSphere: quiz generation from ANY uploaded material, and the
learning assistant.

generate_quiz() returns a dict:
    {"ok": bool, "questions": [...], "source": "gemini" | "demo" | "error",
     "subject": str, "message": str}

IMPORTANT behaviour: the JavaScript demo questions are returned ONLY when the caller
asks for demo mode explicitly. If Gemini is unavailable or fails, ok is False and the
message explains why - we never silently swap in unrelated questions.
"""
import json
import os
import random
import re
import time

import requests

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

QUIZ_PROMPT = """You are writing a quiz for a student, using ONLY the study material below.

Rules:
- Write exactly {n} multiple-choice questions about what THIS material teaches.
- Use only the material. Do not bring in questions from any other subject, even if the
  material looks similar to a well-known course.
- {spread}
- Test understanding (why, how, which, what happens), not trivia about the file itself
  (no questions about page numbers, authors, headings or formatting).
- Exactly four options per question, one clearly correct, three plausible but wrong.
  Do not use "all of the above" / "none of the above". Never mention option letters in
  the explanation.
- Write in the same language as the material.
- "subject" is the name of the course or topic the material is about (1-4 words).
- "topic" is a 2-3 word label for the specific concept each question covers.
- If the material contains no teachable content (for example random characters, a blank
  form, or only a table of contents), return {{"error": "not_educational"}} instead.

Return STRICT JSON only, in exactly this shape (no markdown, no commentary):
{{"subject": "...", "questions": [
  {{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "B", "explanation": "...", "topic": "..."}}
]}}

STUDY MATERIAL:
{material}
"""

# ---- Demo / fallback questions (JavaScript Fundamentals sample material) ----
DEMO_QUESTIONS = [
    {"question": "What does the DOM represent in a web page?",
     "options": {"A": "The server that hosts the page", "B": "A tree of objects representing the page structure",
                 "C": "The CSS rules applied to the page", "D": "The network request log"},
     "answer": "B", "topic": "DOM",
     "explanation": "The Document Object Model is a tree of objects built from the HTML, which JavaScript can read and change."},
    {"question": "Which keyword declares a variable that cannot be reassigned?",
     "options": {"A": "var", "B": "let", "C": "const", "D": "static"},
     "answer": "C", "topic": "ES6 variables",
     "explanation": "const binds a name to a value that cannot be reassigned, although objects it points to can still be mutated."},
    {"question": "What is the result of the expression '5' + 3 in JavaScript?",
     "options": {"A": "8", "B": "'53'", "C": "NaN", "D": "An error"},
     "answer": "B", "topic": "Type coercion",
     "explanation": "The + operator prefers string concatenation when one operand is a string, so the number is coerced to '3'."},
    {"question": "What does addEventListener do?",
     "options": {"A": "Creates a new HTML element", "B": "Sends a request to a server",
                 "C": "Registers a function to run when an event happens", "D": "Pauses script execution"},
     "answer": "C", "topic": "DOM events",
     "explanation": "addEventListener attaches a handler function to an element for a named event such as 'click'."},
    {"question": "Why is async/await used when calling an API with fetch?",
     "options": {"A": "It makes the request faster", "B": "It lets you write asynchronous code that reads sequentially",
                 "C": "It removes the need for error handling", "D": "It converts JSON to HTML automatically"},
     "answer": "B", "topic": "Async JavaScript",
     "explanation": "await pauses inside an async function until the promise settles, so the code reads top-to-bottom while staying non-blocking."},
]


class GeminiError(Exception):
    """Carries a message that is safe to show to the learner."""


def api_key():
    return (os.getenv("GEMINI_API_KEY") or "").strip()


def key_configured():
    key = api_key()
    return bool(key) and key.lower() not in ("your_key_here", "changeme")


def _http_error_message(response):
    detail = ""
    try:
        detail = response.json().get("error", {}).get("message", "")
    except Exception:
        pass
    code = response.status_code
    if code in (400, 403) and "api key" in detail.lower():
        return "Gemini rejected the API key. Check GEMINI_API_KEY in your .env file."
    if code == 403:
        return "Gemini refused the request (HTTP 403). Check that the API key is allowed to use the model."
    if code == 404:
        return "Gemini model '%s' was not found. Check GEMINI_MODEL in your .env file." % MODEL
    if code == 429:
        return "Gemini's free quota is used up for now (HTTP 429). Wait a minute and try again."
    if code >= 500:
        return "Gemini is temporarily unavailable (HTTP %d). Try again shortly." % code
    return "Gemini returned an error (HTTP %d)%s." % (code, ": " + detail[:120] if detail else "")


def call_gemini(prompt=None, contents=None, system=None, temperature=0.4,
                max_tokens=4096, json_mode=False, retries=1):
    """Single place that talks to Gemini. Returns the response text or raises GeminiError."""
    if not key_configured():
        raise GeminiError("The Gemini API key has not been configured. Add GEMINI_API_KEY to "
                          "your .env file and restart the app.")
    body = {
        "contents": contents or [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    last = None
    for attempt in range(retries + 1):
        try:
            response = requests.post(
                ENDPOINT.format(model=MODEL),
                headers={"x-goog-api-key": api_key(), "Content-Type": "application/json"},
                json=body, timeout=60,
            )
        except requests.RequestException:
            last = GeminiError("Could not reach Gemini. Check your internet connection.")
        else:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("promptFeedback", {}).get("blockReason"):
                        raise GeminiError("Gemini declined to process this content.")
                    parts = data["candidates"][0]["content"]["parts"]
                    return "".join(p.get("text", "") for p in parts)
                except GeminiError:
                    raise
                except Exception:
                    last = GeminiError("Gemini returned an empty or unreadable response.")
            else:
                last = GeminiError(_http_error_message(response))
                if response.status_code not in (500, 502, 503, 504):
                    break                      # retrying a bad key or a quota error is pointless
        if attempt < retries:
            time.sleep(1.5)
    raise last


# ------------------------------------------------------------------ quiz generation
_SHUFFLE_BLOCKERS = ("all of the above", "none of the above", "both a and", "a and b", "b and c")


def _shuffle_options(q):
    """Gemini over-uses some answer letters; shuffle so the correct one is not predictable."""
    if any(b in v.lower() for v in q["options"].values() for b in _SHUFFLE_BLOCKERS):
        return q
    correct_text = q["options"][q["answer"]]
    texts = list(q["options"].values())
    random.shuffle(texts)
    q["options"] = dict(zip("ABCD", texts))
    q["answer"] = "ABCD"[texts.index(correct_text)]
    return q


def parse_quiz(raw, n):
    """Validate Gemini's JSON. Returns (subject, questions). Raises ValueError."""
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    obj_start, arr_start = cleaned.find("{"), cleaned.find("[")
    if arr_start != -1 and (obj_start == -1 or arr_start < obj_start):
        data = json.loads(cleaned[arr_start:cleaned.rfind("]") + 1])
    elif obj_start != -1:
        data = json.loads(cleaned[obj_start:cleaned.rfind("}") + 1])
    else:
        raise ValueError("No JSON found in the model response.")

    subject = ""
    if isinstance(data, dict):
        if data.get("error"):
            raise ValueError("not_educational")
        subject = str(data.get("subject", "")).strip()[:60]
        data = data.get("questions", [])

    valid, seen = [], set()
    for q in data:
        opts = q.get("options") or {}
        if not q.get("question") or not {"A", "B", "C", "D"} <= set(opts):
            continue
        if q.get("answer") not in ("A", "B", "C", "D"):
            continue
        texts = [str(opts[k]).strip() for k in "ABCD"]
        key = str(q["question"]).strip().lower()
        if key in seen or len(set(t.lower() for t in texts)) < 4 or not all(texts):
            continue
        seen.add(key)
        valid.append(_shuffle_options({
            "question": str(q["question"]).strip(),
            "options": dict(zip("ABCD", texts)),
            "answer": q["answer"],
            "explanation": str(q.get("explanation", "")).strip(),
            "topic": str(q.get("topic", "General")).strip()[:40] or "General",
        }))
    if len(valid) < 3:
        raise ValueError("The model returned too few usable questions.")
    return subject, valid[:n]


def generate_quiz(material, n_questions=5, spread=False, force_demo=False):
    """Never raises. See the module docstring for the return shape."""
    if force_demo:
        return {"ok": True, "questions": [dict(q) for q in DEMO_QUESTIONS], "source": "demo",
                "subject": "JavaScript",
                "message": "Demo mode: showing 5 prepared JavaScript questions."}
    spread_rule = ("The material is given in several numbered parts. Spread the questions across "
                   "different parts so the whole document is covered." if spread else
                   "Cover different ideas from the material rather than repeating one point.")
    prompt = QUIZ_PROMPT.format(n=n_questions, spread=spread_rule, material=material)
    try:
        raw = call_gemini(prompt=prompt, temperature=0.4, max_tokens=6144, json_mode=True)
        try:
            subject, questions = parse_quiz(raw, n_questions)
        except (ValueError, KeyError, TypeError) as exc:
            if str(exc) == "not_educational":
                raise GeminiError("That document does not contain enough teachable content to "
                                  "build a quiz from. Try a chapter, notes or slides.")
            # one retry: the model occasionally returns malformed JSON
            raw = call_gemini(prompt=prompt, temperature=0.2, max_tokens=6144, json_mode=True)
            subject, questions = parse_quiz(raw, n_questions)
        return {"ok": True, "questions": questions, "source": "gemini", "subject": subject,
                "message": "Quiz generated from your material by Gemini."}
    except GeminiError as exc:
        return {"ok": False, "questions": [], "source": "error", "subject": "", "message": str(exc)}
    except Exception:
        return {"ok": False, "questions": [], "source": "error", "subject": "",
                "message": "Gemini returned a quiz we could not read. Please try again - "
                           "or run the demo quiz."}
