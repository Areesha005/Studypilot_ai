
import re
from datetime import date

import streamlit as st
from pdf_agent import (
    extract_pdf_text,
    generate_flashcards,
    generate_quiz,
)


# -------------------- PAGE CONFIG --------------------

st.set_page_config(
    page_title="StudyPilot AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -------------------- STYLING --------------------

st.markdown(
    """
    <style>
    .stApp {
        background: #f5f7fb;
    }

    [data-testid="stSidebar"] {
        background: #eef2ff;
    }

    .hero {
        background: linear-gradient(120deg, #2457e6, #753be8);
        color: white;
        padding: 28px;
        border-radius: 18px;
        margin-bottom: 22px;
    }

    .hero h1 {
        color: white;
        margin-bottom: 8px;
    }

    .hero p {
        color: #f0f2ff;
        font-size: 16px;
    }

    .metric-card {
        background: white;
        padding: 18px;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        margin-bottom: 12px;
    }

    .metric-label {
        color: #64748b;
        font-size: 14px;
    }

    .metric-value {
        color: #172554;
        font-size: 27px;
        font-weight: 700;
    }

    .section-note {
        color: #64748b;
        font-size: 14px;
    }

    div.stButton > button[kind="primary"] {
        background: #4f46e5;
        border: none;
    }
    
/* Improve readability throughout the dashboard */
.stApp,
.stApp p,
.stApp label,
.stApp li,
.stMarkdown,
[data-testid="stWidgetLabel"] {
    color: #1f2937 !important;
}

/* Make headings dark and clear */
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4 {
    color: #172554 !important;
}

/* Make the tab names readable */
.stTabs [data-baseweb="tab"] {
    color: #334155 !important;
}

.stTabs [data-baseweb="tab"] p {
    color: #334155 !important;
    font-weight: 600 !important;
}

.stTabs [aria-selected="true"] p {
    color: #4338ca !important;
}

/* Keep the gradient banner text white */
.hero,
.hero h1,
.hero p {
    color: #ffffff !important;
}

/* Make the footer visible */
.stApp footer,
.stApp footer p {
    color: #64748b !important;
}

/* Improve input text visibility */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    color: #172554 !important;
    background-color: #ffffff !important;
}

/* Make buttons readable */
.stButton > button {
    background-color: #4f46e5 !important;
    color: #ffffff !important;
    border: 1px solid #4338ca !important;
    border-radius: 10px !important;
}

.stButton > button p,
.stButton > button span {
    color: #ffffff !important;
}

/* Disabled buttons remain readable */
.stButton > button:disabled {
    background-color: #e2e8f0 !important;
    color: #64748b !important;
    border-color: #cbd5e1 !important;
    opacity: 1 !important;
}

.stButton > button:disabled p,
.stButton > button:disabled span {
    color: #64748b !important;
}

    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------- SESSION STATE --------------------

defaults = {
    "student_name": "Student",
    "study_hours": 3,
    "study_goal": "Prepare for upcoming exams",
    "topics_text": "",
    "completed_topics": [],
    "pdf_text": "",
    "pdf_name": "",
    "quiz": [],
    "quiz_results": [],
    "flashcards": [],
    "flashcard_index": 0,
    "show_answer": False,
    "knowledge_gaps": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.markdown("## 📚 StudyPilot AI")
    st.caption("Your personal study companion")
    st.divider()

    st.text_input(
        "Student name",
        key="student_name",
        max_chars=60,
    )

    st.number_input(
        "Daily study target (hours)",
        min_value=1,
        max_value=16,
        key="study_hours",
        step=1,
    )

    st.text_input(
        "Current study goal",
        key="study_goal",
        max_chars=150,
    )

    st.divider()
    st.caption("Your progress is stored for this app session.")
    st.caption("Today: " + date.today().strftime("%d %b %Y"))


# -------------------- HELPERS --------------------

def show_metric(label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def clean_answer(value):
    return re.sub(r"\s+", " ", value.strip()).lower()


# -------------------- HEADER --------------------

student_name = st.session_state.student_name.strip() or "Student"

st.markdown(
    f"""
    <div class="hero">
        <h1>Welcome back, {student_name} 👋</h1>
        <p>Your learning journey, organized in one place.</p>
        <p>Set your goals, plan your studies, and revise smarter.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

overview_tab, planner_tab, pdf_tab, gaps_tab, flash_tab = st.tabs(
    [
        "🏠 Overview",
        "🗓️ Study Planner",
        "📄 PDF Studio",
        "🎯 Knowledge Gaps",
        "🃏 Flashcards",
    ]
)


# ====================================================
# 1. OVERVIEW
# ====================================================

with overview_tab:
    st.subheader("Your learning dashboard")
    st.write("Here's a quick look at your study activity.")

    total_topics = len(
        [
            topic.strip()
            for topic in st.session_state.topics_text.splitlines()
            if topic.strip()
        ]
    )

    completed_count = len(st.session_state.completed_topics)

    col1, col2, col3 = st.columns(3)

    with col1:
        show_metric("Daily study target", f"{st.session_state.study_hours} hrs")

    with col2:
        show_metric("Topics completed", completed_count)

    with col3:
        show_metric("Topics in plan", total_topics)

    if total_topics:
        progress = min(completed_count / total_topics, 1.0)
        st.markdown("### Study progress")
        st.progress(progress)
        st.caption(f"{round(progress * 100)}% of your listed topics completed.")
    else:
        st.info(
            "Your study plan is empty. Open Study Planner to add your topics."
        )

    st.markdown("### Your current goal")
    st.write(st.session_state.study_goal)

    st.markdown("### Quick actions")
    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Open Study Planner", use_container_width=True):
            st.info("Select the Study Planner tab above.")

    with col_b:
        if st.button("Open PDF Studio", use_container_width=True):
            st.info("Select the PDF Studio tab above.")

    st.caption(
        "StudyPilot AI currently uses local study tools. "
        "An external AI service is not connected in this version."
    )


# ====================================================
# 2. STUDY PLANNER
# ====================================================

with planner_tab:
    st.subheader("Build your study plan")
    st.write("Add one topic per line, then mark topics as completed.")

    with st.form("planner_form"):
        new_topics = st.text_area(
            "Study topics",
            value=st.session_state.topics_text,
            height=150,
            placeholder=(
                "Example:\n"
                "Engineering Mathematics\n"
                "Programming in C\n"
                "Applied Physics"
            ),
        )

        save_plan = st.form_submit_button(
            "Save study plan",
            type="primary",
        )

    if save_plan:
        old_topics = {
            topic.strip()
            for topic in st.session_state.topics_text.splitlines()
            if topic.strip()
        }
        new_topic_set = {
            topic.strip()
            for topic in new_topics.splitlines()
            if topic.strip()
        }

        st.session_state.topics_text = new_topics

        # Keep completion records for topics that still exist.
        st.session_state.completed_topics = [
            topic
            for topic in st.session_state.completed_topics
            if topic in new_topic_set
        ]

        st.success("Your study plan has been saved.")

    topics = [
        topic.strip()
        for topic in st.session_state.topics_text.splitlines()
        if topic.strip()
    ]

    
    if topics:
        st.markdown("### Today's checklist")

        completed_topics = set(st.session_state.completed_topics)

        for index, topic in enumerate(topics):
            key = f"planner_topic_{index}_{topic}"

            if key not in st.session_state:
                st.session_state[key] = topic in completed_topics

            def update_topic(topic_name=topic, widget_key=key):
                current = set(st.session_state.completed_topics)

                if st.session_state[widget_key]:
                    current.add(topic_name)
                else:
                    current.discard(topic_name)

                st.session_state.completed_topics = list(current)

            st.checkbox(
                topic,
                key=key,
                on_change=update_topic,
            )

        completed = sum(
            topic in st.session_state.completed_topics
            for topic in topics
        )

        st.progress(completed / len(topics))
        st.caption(f"{completed} of {len(topics)} topics completed.")
    else:
        st.info("Add your first topic above to begin planning.")



# ====================================================
# 3. PDF STUDIO
# ====================================================

with pdf_tab:
    st.subheader("PDF Studio")
    st.write(
        "Upload a text-based PDF to extract its content, "
        "create a simple quiz, and make revision cards."
    )

    uploaded_pdf = st.file_uploader(
        "Upload study material",
        type=["pdf"],
        key="study_pdf_upload",
    )

    if uploaded_pdf is not None:
        if st.button("Extract PDF text", type="primary"):
            try:
                extracted = extract_pdf_text(uploaded_pdf)

                st.session_state.pdf_text = extracted
                st.session_state.pdf_name = uploaded_pdf.name
                st.session_state.quiz = []
                st.session_state.quiz_results = []
                st.session_state.flashcards = []
                st.session_state.flashcard_index = 0
                st.session_state.show_answer = False

                st.success("PDF text extracted successfully.")

            except (ValueError, TypeError) as exc:
                st.error(str(exc))

            except Exception:
                st.error(
                    "Something went wrong while processing this PDF. "
                    "Please try another file."
                )

    if st.session_state.pdf_text:
        st.markdown("### Extracted document")
        st.caption(f"File: {st.session_state.pdf_name}")

        st.text_area(
            "Extracted text",
            value=st.session_state.pdf_text,
            height=220,
            disabled=True,
            key="extracted_text_display",
        )

        word_count = len(st.session_state.pdf_text.split())
        st.caption(f"Approximate word count: {word_count}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Generate quiz", use_container_width=True):
                st.session_state.quiz = generate_quiz(
                    st.session_state.pdf_text,
                    limit=10,
                )
                st.session_state.quiz_results = []
                st.success(
                    f"Created {len(st.session_state.quiz)} quiz questions."
                )

        with col2:
            if st.button("Generate flashcards", use_container_width=True):
                st.session_state.flashcards = generate_flashcards(
                    st.session_state.pdf_text,
                    limit=10,
                )
                st.session_state.flashcard_index = 0
                st.session_state.show_answer = False
                st.success(
                    f"Created {len(st.session_state.flashcards)} flashcards."
                )

        if st.session_state.quiz:
            st.markdown("### PDF quiz")

            with st.form("pdf_quiz_form"):
                user_answers = []

                for index, question in enumerate(st.session_state.quiz):
                    answer = st.text_input(
                        f"Question {index + 1}: {question['question']}",
                        key=f"pdf_answer_{index}",
                    )
                    user_answers.append(answer)

                submitted = st.form_submit_button(
                    "Check answers",
                    type="primary",
                )

            if submitted:
                results = []

                for question, answer in zip(
                    st.session_state.quiz,
                    user_answers,
                ):
                    correct = (
                        clean_answer(answer)
                        == clean_answer(question["answer"])
                    )

                    results.append({
                        "question": question["question"],
                        "your_answer": answer,
                        "correct_answer": question["answer"],
                        "correct": correct,
                    })

                st.session_state.quiz_results = results

                st.session_state.knowledge_gaps = [
                    result for result in results
                    if not result["correct"]
                ]

            if st.session_state.quiz_results:
                score = sum(
                    result["correct"]
                    for result in st.session_state.quiz_results
                )
                total = len(st.session_state.quiz_results)

                st.markdown(f"### Score: {score}/{total}")

                for result in st.session_state.quiz_results:
                    if result["correct"]:
                        st.success(
                            f"Correct: {result['question']}"
                        )
                    else:
                        st.warning(
                            f"Question: {result['question']}\n\n"
                            f"Your answer: {result['your_answer'] or 'No answer'}\n\n"
                            f"Expected answer: {result['correct_answer']}"
                        )

        if not st.session_state.quiz:
            st.caption("Generate a quiz to practise recall.")

    else:
        st.info("Upload a PDF and select Extract PDF text to get started.")


# ====================================================
# 4. KNOWLEDGE GAPS
# ====================================================

with gaps_tab:
    st.subheader("Knowledge Gaps")
    st.write(
        "Review questions you answered incorrectly in your most recent quiz."
    )

    gaps = st.session_state.knowledge_gaps

    if gaps:
        st.markdown(f"### Areas to revise: {len(gaps)}")

        for index, gap in enumerate(gaps, start=1):
            with st.expander(f"Revision item {index}"):
                st.write("**Question**")
                st.write(gap["question"])

                st.write("**Your answer**")
                st.write(gap["your_answer"] or "No answer provided")

                st.write("**Expected answer**")
                st.write(gap["correct_answer"])

        if st.button("Clear knowledge gaps"):
            st.session_state.knowledge_gaps = []
            st.rerun()
    else:
        st.info(
            "No knowledge gaps recorded yet. Complete a PDF quiz "
            "to identify topics you may need to revise."
        )


# ====================================================
# 5. FLASHCARDS
# ====================================================

with flash_tab:
    st.subheader("Flashcards")
    st.write("Use your cards for quick revision.")

    cards = st.session_state.flashcards

    if cards:
        total_cards = len(cards)

        st.caption(
            f"Card {st.session_state.flashcard_index + 1} of {total_cards}"
        )

        card = cards[st.session_state.flashcard_index]

        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Study card</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Question")
        st.write(card["question"])

        if st.session_state.show_answer:
            st.markdown("### Answer")
            st.info(card["answer"])

        if st.button(
            "Hide answer" if st.session_state.show_answer else "Show answer",
            use_container_width=True,
        ):
            st.session_state.show_answer = (
                not st.session_state.show_answer
            )
            st.rerun()

        col_prev, col_next = st.columns(2)

        with col_prev:
            if st.button(
                "← Previous",
                disabled=st.session_state.flashcard_index == 0,
                use_container_width=True,
            ):
                st.session_state.flashcard_index -= 1
                st.session_state.show_answer = False
                st.rerun()

        with col_next:
            if st.button(
                "Next →",
                disabled=(
                    st.session_state.flashcard_index >= total_cards - 1
                ),
                use_container_width=True,
            ):
                st.session_state.flashcard_index += 1
                st.session_state.show_answer = False
                st.rerun()

    else:
        st.info(
            "No flashcards yet. Open PDF Studio, upload a PDF, "
            "extract its text, and select Generate flashcards."
        )


# -------------------- FOOTER --------------------

st.divider()
st.caption(
    "StudyPilot AI • Learn smarter, one step at a time."
)
