import json
import os
from pathlib import Path

import streamlit as st
from google import genai
from google.genai import errors

ROOT = Path(__file__).parent
CURRICULUM = json.loads((ROOT / "data/courses/curriculum.json").read_text(encoding="utf-8"))
LESSONS = json.loads((ROOT / "data/lessons/lessons.json").read_text(encoding="utf-8"))

st.set_page_config(page_title="CodePath Academy", page_icon="📘", layout="wide")

st.markdown("""
<style>
:root { color-scheme: light; }
html, body, [class*="css"] { font-family: Arial, Helvetica, sans-serif !important; }
.stApp { background: #ffffff; color: #172b3a; }
.block-container { max-width: 1500px; padding: 1.4rem 2rem 4rem 2rem; }
[data-testid="stSidebar"] { background: #f1f5f9; border-right: 1px solid #cbd5e1; }
[data-testid="stSidebar"] * { color: #172b3a; }
h1, h2, h3, h4, p, label, li { color: #172b3a; }
h1 { font-size: 2.35rem !important; font-weight: 750 !important; letter-spacing: -0.035em; }
h2 { font-size: 1.65rem !important; font-weight: 700 !important; margin-top: 1.6rem !important; }
h3 { font-size: 1.2rem !important; font-weight: 700 !important; }
p, li { line-height: 1.75; }
.brand { font-size: 1.35rem; font-weight: 800; color: #087f5b; }
.brand span { color: #172b3a; }
.eyebrow { color: #087f5b; font-size: .76rem; font-weight: 800; letter-spacing: .13em; text-transform: uppercase; }
.lesson-intro { background: #ecfdf5; border-left: 5px solid #059669; padding: 1.15rem 1.35rem; border-radius: 5px; line-height: 1.85; color: #163b30; }
.lesson-copy { font-size: 1.04rem; line-height: 1.9; color: #263b4d; }
.note { background: #eff6ff; border-left: 4px solid #2563eb; padding: .9rem 1.1rem; border-radius: 5px; color: #1e3a5f; }
.small-muted { color: #64748b; font-size: .9rem; }
div.stButton > button { border-radius: 5px; border: 1px solid #cbd5e1; background: #fff; color: #172b3a; min-height: 2.55rem; font-weight: 600; }
div.stButton > button:hover { border-color: #059669; color: #047857; background: #f0fdf4; }
[data-testid="stCode"] { border: 1px solid #d7e0e8; border-radius: 7px; }
[data-testid="stChatMessage"] { border: 1px solid #dce5ec; border-radius: 8px; background: #f8fafc; }
[data-testid="stChatInput"] { border-color: #94a3b8 !important; }
[data-testid="stChatInput"]:focus-within { border-color: #059669 !important; box-shadow: 0 0 0 1px #059669; }
hr { border-color: #dbe3ea; }
</style>
""", unsafe_allow_html=True)

st.session_state.setdefault("course", "python")
st.session_state.setdefault("topic", "Introduction to Python")
st.session_state.setdefault("page", "Home")
st.session_state.setdefault("chat_history", [])

def topics_for(course):
    return [(section["name"], topic) for section in CURRICULUM[course]["sections"] for topic in section["topics"]]

def navigate(page, course=None, topic=None):
    if course is not None:
        st.session_state.course = course
    if topic is not None:
        st.session_state.topic = topic
    st.session_state.page = page
    st.rerun()

def get_api_key():
    # Read secrets safely; missing secrets.toml must never crash the app.
    try:
        secret = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        secret = ""
    return os.getenv("GEMINI_API_KEY", "").strip() or str(secret).strip()

def ask_gemini(question, course, topic, history):
    api_key = get_api_key()
    if not api_key:
        return ("**The AI tutor is not connected yet.** The deployment is missing its private "
                "GEMINI_API_KEY secret. Add it in Streamlit app settings, then reboot the app.")

    lesson = LESSONS.get(course, {}).get(topic, {})
    client = genai.Client(api_key=api_key)
    system_context = f"""
You are the CodePath Academy programming tutor. Teach accurately and patiently, using original explanations.
Use clear beginner-friendly English. For a concept question, explain: definition, why it is used, how it works,
syntax, a topic-specific code example, line-by-line explanation, and expected output.
For debugging, identify the exact cause, show corrected code, and explain the fix.
Do not claim that code was executed unless it was actually executed. If uncertain, say so.
Current course: {CURRICULUM[course]['title']}
Current topic: {topic}
Course lesson concept: {lesson.get('concept', '')}
Course lesson syntax: {lesson.get('syntax', '')}
Course lesson example: {lesson.get('example', '')}
Course lesson output: {lesson.get('output', '')}
"""
    # Gemini chat history uses "user" and "model" roles, not "assistant".
    contents = []
    for item in history[-8:]:
        role = "model" if item["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": item["content"]}]})
    contents.append({"role": "user", "parts": [{"text": question}]})

    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    # Retry temporary capacity errors; optionally use a fallback model from secrets.
    try:
        fallback = str(st.secrets.get("GEMINI_FALLBACK_MODEL", "")).strip()
    except Exception:
        fallback = os.getenv("GEMINI_FALLBACK_MODEL", "").strip()

    models_to_try = [model]
    if fallback and fallback != model:
        models_to_try.append(fallback)

    last_error = None
    for candidate in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=candidate,
                    contents=contents,
                    config={"system_instruction": system_context, "temperature": 0.4},
                )
                return response.text or "I couldn't generate a response. Please try again."
            except Exception as exc:
                last_error = exc
                message = str(exc)
                low = message.lower()
                if "401" in message or "unauthenticated" in low or "api key not valid" in low or "invalid api key" in low:
                    return ("**Gemini authentication failed (401).** The key stored in Streamlit Secrets "
                            "is not accepted. Create a fresh Gemini API key in Google AI Studio, replace "
                            "the secret, and reboot the app. Never share the key or commit it to GitHub.")
                if "403" in message or "permission" in low:
                    return ("**Gemini access denied (403).** Check that the API key belongs to a project "
                            "with Gemini API access enabled.")
                if "404" in message or "not_found" in low:
                    break
                retryable = any(code in message for code in ("503", "429", "500", "502", "504", "408"))
                if not retryable:
                    return f"**Gemini request failed.** {type(exc).__name__}: {message}"
                if attempt < 2:
                    import time
                    time.sleep(2 ** (attempt + 1))

    if last_error:
        message = str(last_error)
        if "503" in message or "UNAVAILABLE" in message:
            return ("**Gemini is temporarily busy (503).** Your API key is being accepted, but Google's "
                    "model servers are currently overloaded. The app retried automatically. Please try "
                    "again in a minute, or configure GEMINI_FALLBACK_MODEL in Streamlit Secrets.")
        if "404" in message or "not_found" in message.lower():
            return (f"**Gemini model not found.** Check that {model} is available for your API key, "
                    "or set GEMINI_MODEL to a model listed in Google AI Studio.")
        return f"**Gemini request failed.** {type(last_error).__name__}: {last_error}"
    return "The AI tutor could not get a response. Please try again."

def show_header():
    left, right1, right2 = st.columns([6, 1, 1])
    with left:
        st.markdown('<div class="brand">📘 RoadMap <span></span></div><div class="small-muted">Programming tutorials for everyone</div>', unsafe_allow_html=True)
    with right1:
        if st.button("All courses", use_container_width=True):
            navigate("Courses")
    with right2:
        if st.button("AI Tutor", use_container_width=True):
            navigate("Tutor")

with st.sidebar:
    st.markdown('<div class="brand">📘 RoadMap <span></span></div>', unsafe_allow_html=True)
    st.caption("LEARN • PRACTISE • BUILD")
    if st.button("⌂  Home", use_container_width=True):
        navigate("Home")
    if st.button("▦  All courses", use_container_width=True):
        navigate("Courses")
    st.divider()
    course_keys = list(CURRICULUM.keys())
    selected_course = st.selectbox(
        "SELECT COURSE", course_keys,
        index=course_keys.index(st.session_state.course),
        format_func=lambda key: CURRICULUM[key]["title"]
    )
    if selected_course != st.session_state.course:
        navigate("Course", selected_course, topics_for(selected_course)[0][1])
    st.markdown("**COURSE CONTENTS**")
    for section in CURRICULUM[st.session_state.course]["sections"]:
        active = st.session_state.topic in section["topics"]
        with st.expander(section["name"], expanded=active):
            for topic in section["topics"]:
                marker = "●" if topic == st.session_state.topic and st.session_state.page == "Lesson" else "○"
                if st.button(f"{marker}  {topic}", key=f"nav_{st.session_state.course}_{topic}", use_container_width=True):
                    navigate("Lesson", st.session_state.course, topic)
    st.divider()
    if st.button("💬  AI Programming Tutor", use_container_width=True):
        navigate("Tutor")
    st.caption("Study each chapter in order.")

show_header()
page = st.session_state.page
course = st.session_state.course
course_info = CURRICULUM[course]

if page == "Home":
    st.markdown('<div class="eyebrow">WELCOME TO ROADMAP</div>', unsafe_allow_html=True)
    st.title("Learn to code, one concept at a time.")
    st.write("Choose a course. Read the explanation. Study the syntax. Follow the example and practise.")
    st.markdown("## Explore programming courses")
    cols = st.columns(3)
    for i, (key, info) in enumerate(CURRICULUM.items()):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### {info['title']}")
                st.write(info["description"])
                total = sum(len(sec["topics"]) for sec in info["sections"])
                st.caption(f"{total} chapters · {len(info['sections'])} sections")
                if st.button("Start learning →", key=f"start_{key}", use_container_width=True):
                    navigate("Course", key, topics_for(key)[0][1])

elif page == "Courses":
    st.markdown('<div class="eyebrow">COURSE LIBRARY</div>', unsafe_allow_html=True)
    st.title("All programming courses")
    st.write("Select a course to view its complete chapter list.")
    for key, info in CURRICULUM.items():
        with st.container(border=True):
            a, b = st.columns([5, 1])
            with a:
                st.markdown(f"### {info['title']}")
                st.write(info["description"])
                st.caption(f"{sum(len(sec['topics']) for sec in info['sections'])} chapters")
            with b:
                if st.button("Open →", key=f"open_{key}"):
                    navigate("Course", key, topics_for(key)[0][1])

elif page == "Course":
    st.markdown('<div class="eyebrow">COURSE CONTENTS</div>', unsafe_allow_html=True)
    st.title(course_info["title"])
    st.write(course_info["description"])
    for section in course_info["sections"]:
        with st.expander(f"{section['name']} · {len(section['topics'])} chapters", expanded=True):
            for number, topic in enumerate(section["topics"], 1):
                if st.button(f"{number:02d}   {topic}   →", key=f"chapter_{course}_{section['name']}_{topic}", use_container_width=True):
                    navigate("Lesson", course, topic)

elif page == "Lesson":
    topic = st.session_state.topic
    lesson = LESSONS.get(course, {}).get(topic)
    st.markdown(f'<div class="eyebrow">{course_info["title"]}  /  {lesson.get("section", "Tutorial") if lesson else "Tutorial"}</div>', unsafe_allow_html=True)
    st.title(topic)
    if not lesson:
        st.error("Lesson content is missing for this chapter.")
    else:
        st.markdown(f'<div class="lesson-intro"><b>What is {topic}?</b><br>{lesson["concept"]}</div>', unsafe_allow_html=True)
        st.markdown("## Why is it used?")
        st.markdown(f'<div class="lesson-copy">{lesson["why"]}</div>', unsafe_allow_html=True)
        st.markdown("## How does it work?")
        st.markdown(f'<div class="lesson-copy">{lesson["how"]}</div>', unsafe_allow_html=True)
        st.markdown("## Syntax")
        st.code(lesson["syntax"], language={"python":"python","java":"java","c":"c","cpp":"cpp","html":"html","css":"css","javascript":"javascript"}[course])
        st.markdown("## Example")
        st.code(lesson["example"], language={"python":"python","java":"java","c":"c","cpp":"cpp","html":"html","css":"css","javascript":"javascript"}[course])
        st.markdown("## Explanation of the example")
        st.write(lesson["example_explanation"])
        st.markdown("## Output")
        st.code(lesson["output"], language="text")
        st.markdown('<div class="note"><b>Study tip:</b> Change one value in the example, run it again, and compare the output.</div>', unsafe_allow_html=True)
        ordered = [name for _, name in topics_for(course)]
        index = ordered.index(topic)
        prev_col, next_col, tutor_col = st.columns(3)
        with prev_col:
            if index > 0 and st.button("← Previous chapter", use_container_width=True):
                navigate("Lesson", course, ordered[index - 1])
        with next_col:
            if index < len(ordered) - 1 and st.button("Next chapter →", use_container_width=True):
                navigate("Lesson", course, ordered[index + 1])
        with tutor_col:
            if st.button("Ask AI about this topic", use_container_width=True):
                navigate("Tutor", course, topic)

elif page == "Tutor":
    st.markdown('<div class="eyebrow">PERSONAL PROGRAMMING ASSISTANT</div>', unsafe_allow_html=True)
    st.title("AI Programming Tutor")
    st.write("Ask about a programming concept, request a new example, or paste code for explanation and debugging.")
    st.caption(f"Current learning context: {course_info['title']} · {st.session_state.topic}")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("Ask your programming question...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Preparing your explanation..."):
                answer = ask_gemini(prompt, course, st.session_state.topic, st.session_state.chat_history[:-1])
            st.markdown(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
    if st.button("Clear conversation"):
        st.session_state.chat_history = []
        st.rerun()
