"""SkillSphere assistant: a Gemini chat that is grounded in the learner's own data."""
import ai

SYSTEM = """You are the SkillSphere Assistant, a learning coach inside SkillSphere AI - a platform that
helps a learner find the skills they lack for a target role, learn them, practise them, test
themselves with quizzes and stay motivated with XP, levels, badges and streaks.

You can see this learner's SkillSphere data below. Use it whenever it helps: refer to their target
role, skill gaps, quiz scores, weak topics and progress. Never invent data that is not listed.
If something is not in the data (for example no quizzes yet), say so and suggest the next step.

What you help with:
- What to learn next and why (explain skill gaps using the data: the role needs the skill and the
  learner's level for it is low or zero).
- Explaining programming and computer-science concepts clearly, with a short example.
- Practice: suggest an exercise or point to the Problems page; the learner earns XP there.
- Revision plans after weak quiz results; explaining a specific quiz question when it is given.
- What skills a role needs.

Style: warm, direct, concise (usually under 180 words). Plain text with short paragraphs; use
`code` for code and **bold** sparingly; short lists are fine. Point to SkillSphere pages by name
(Skill gaps, Learning, Problems, AI quiz, Dashboard) rather than inventing links.
If asked about something unrelated to learning, careers or skills, politely steer back.
Be honest: if you are unsure, say so.

LEARNER DATA
{context}
"""

MAX_MESSAGE = 1500
MAX_HISTORY = 8


def reply(context, message, history=None):
    """Returns {"ok": bool, "reply": str}."""
    message = (message or "").strip()[:MAX_MESSAGE]
    if not message:
        return {"ok": False, "reply": "Type a question first."}
    contents = []
    for turn in (history or [])[-MAX_HISTORY:]:
        role = "model" if turn.get("role") in ("assistant", "model") else "user"
        text = str(turn.get("text", ""))[:2000]
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})
    contents.append({"role": "user", "parts": [{"text": message}]})
    # Gemini requires the conversation to start with a user turn and alternate sensibly.
    while contents and contents[0]["role"] != "user":
        contents.pop(0)
    try:
        text = ai.call_gemini(contents=contents, system=SYSTEM.format(context=context),
                              temperature=0.5, max_tokens=1024)
    except ai.GeminiError as exc:
        return {"ok": False, "reply": str(exc)}
    return {"ok": True, "reply": text.strip() or "I could not come up with an answer - try rephrasing."}
