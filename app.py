# Windows asyncio compatibility: avoid Proactor socket cleanup errors
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
import time
import os
import tempfile
from dotenv import load_dotenv
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

/* ── Root Variables ── */
:root {
    --bg: #0a0a0f;
    --surface: #111118;
    --surface-2: #1a1a25;
    --border: #2a2a3a;
    --accent: #7c3aed;
    --accent-glow: #9f67ff;
    --accent-2: #06b6d4;
    --text: #e8e8f0;
    --text-muted: #7070a0;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.stApp {
    background: var(--bg) !important;
}

/* Animated grid background */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image:
        linear-gradient(rgba(124, 58, 237, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(124, 58, 237, 0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Syne', sans-serif !important;
    color: var(--text) !important;
}

/* ── Hero Title ── */
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 800;
    line-height: 1.1;
    margin: 0;
    background: linear-gradient(135deg, #ffffff 0%, var(--accent-glow) 50%, var(--accent-2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-muted);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

/* ── Cards ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}

.card:hover {
    border-color: var(--accent);
}

.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, var(--accent), var(--accent-2));
}

.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.card-content {
    font-size: 0.875rem;
    line-height: 1.7;
    color: var(--text);
}

/* ── Accent Badge ── */
.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.badge-purple { background: rgba(124,58,237,0.2); color: var(--accent-glow); border: 1px solid rgba(124,58,237,0.3); }
.badge-cyan   { background: rgba(6,182,212,0.15); color: var(--accent-2);    border: 1px solid rgba(6,182,212,0.3); }
.badge-green  { background: rgba(16,185,129,0.15); color: var(--success);    border: 1px solid rgba(16,185,129,0.3); }

/* ── Input & Buttons ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(124,58,237,0.2) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), #5b21b6) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s !important;
    text-transform: uppercase !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(124,58,237,0.4) !important;
}

/* Secondary button */
.stButton > button[kind="secondary"] {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
}

/* ── Progress / Status ── */
.status-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--surface-2);
    border-radius: 8px;
    margin: 0.4rem 0;
    border: 1px solid var(--border);
    font-size: 0.8rem;
}

.status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

.dot-active   { background: var(--accent-glow); box-shadow: 0 0 8px var(--accent-glow); animation: pulse 1.5s infinite; }
.dot-done     { background: var(--success); }
.dot-pending  { background: var(--border); }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}

/* ── Chat ── */
.chat-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    max-height: 420px;
    overflow-y: auto;
    margin-bottom: 1rem;
}

.chat-msg {
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}

.chat-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

.chat-bubble {
    display: inline-block;
    padding: 0.6rem 1rem;
    border-radius: 10px;
    font-size: 0.85rem;
    line-height: 1.6;
    max-width: 90%;
}

.user-label  { color: var(--accent-glow); }
.bot-label   { color: var(--accent-2); }

.user-bubble { background: rgba(124,58,237,0.15); border: 1px solid rgba(124,58,237,0.25); align-self: flex-end; }
.bot-bubble  { background: rgba(6,182,212,0.1);  border: 1px solid rgba(6,182,212,0.2);   align-self: flex-start; }

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ── Transcript box ── */
.transcript-box {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem;
    font-size: 0.82rem;
    line-height: 1.8;
    max-height: 300px;
    overflow-y: auto;
    color: var(--text-muted);
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Stale Streamlit elements ── */
.stProgress > div > div > div { background: var(--accent) !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }
[data-testid="stMarkdownContainer"] p { color: var(--text) !important; }
label { color: var(--text-muted) !important; font-size: 0.8rem !important; }

/* scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── Pipeline Tracker (animated stepper) ── */
.pipeline-track {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem 1rem 1rem 1rem;
    margin: 0.5rem 0 1.5rem 0;
}
.pipeline-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    flex: 1;
    position: relative;
}
.pipeline-step:not(:last-child)::after {
    content: '';
    position: absolute;
    top: 15px;
    left: 55%;
    width: 90%;
    height: 2px;
    background: var(--border);
    z-index: 0;
    transition: background 0.4s ease;
}
.pipeline-step.done:not(:last-child)::after { background: var(--success); }
.pipeline-circle {
    width: 30px; height: 30px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem;
    background: var(--surface-2);
    border: 2px solid var(--border);
    z-index: 1;
    transition: all 0.3s ease;
}
.pipeline-step.active .pipeline-circle {
    border-color: var(--accent-glow);
    background: radial-gradient(circle, var(--accent), #5b21b6);
    box-shadow: 0 0 14px var(--accent-glow);
    animation: pulse 1.3s infinite;
}
.pipeline-step.done .pipeline-circle {
    border-color: var(--success);
    background: rgba(16,185,129,0.2);
}
.pipeline-label {
    font-size: 0.62rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    text-align: center;
    transition: color 0.3s ease;
}
.pipeline-step.active .pipeline-label,
.pipeline-step.done .pipeline-label { color: var(--text); }

/* ── Native chat elements re-skinned ── */
[data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 0.25rem 0.5rem !important;
    margin-bottom: 0.6rem !important;
}
[data-testid="stChatInput"] textarea {
    background: var(--surface-2) !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
    border-radius: 10px !important;
}
[data-testid="stChatInput"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    background: var(--surface) !important;
}

/* ── Code blocks (used for copy-able results) ── */
.stCodeBlock, pre {
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
}
code {
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── Radio / segmented control ── */
div[role="radiogroup"] {
    gap: 0.4rem !important;
}
div[role="radiogroup"] label {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.35rem 0.9rem !important;
    transition: all 0.2s ease;
}
div[role="radiogroup"] label:hover { border-color: var(--accent); }

/* ── File uploader ── */
[data-testid="stFileUploaderDropzone"] {
    background: var(--surface-2) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--accent) !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 0.25rem; }
.stTabs [data-baseweb="tab"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px 8px 0 0;
    color: var(--text-muted);
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.8rem;
    letter-spacing: 0.04em;
}
.stTabs [aria-selected="true"] {
    color: var(--text) !important;
    border-bottom: 2px solid var(--accent) !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    border-color: var(--accent-2) !important;
    color: var(--accent-2) !important;
}

/* ── How-it-works mini steps (empty state) ── */
.hiw-row { display:flex; gap:1rem; justify-content:center; flex-wrap:wrap; margin-top: 2.5rem; }
.hiw-step {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    width: 180px;
    text-align: center;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.hiw-step:hover { transform: translateY(-3px); border-color: var(--accent); }
.hiw-num {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    color: var(--accent-glow);
    font-size: 0.75rem;
    letter-spacing: 0.1em;
}
.hiw-title { font-family:'Syne',sans-serif; font-weight:700; font-size:0.85rem; margin: 0.3rem 0; }
.hiw-desc { font-size: 0.72rem; color: var(--text-muted); line-height:1.5; }

/* Card fade-in */
.card { animation: fadein 0.4s ease; }
@keyframes fadein { from { opacity:0; transform: translateY(6px);} to {opacity:1; transform:translateY(0);} }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ──────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

PIPELINE_STAGES = [
    ("audio",      "🔊", "Audio"),
    ("transcript", "📝", "Transcript"),
    ("title",      "🏷️", "Title"),
    ("summary",    "📋", "Summary"),
    ("extract",    "🔍", "Extract"),
    ("rag",        "🧠", "RAG Index"),
]

# ─── Helpers ────────────────────────────────────────────────────────────────────
def step_status(steps: dict, key: str) -> str:
    s = steps.get(key, "pending")
    if s == "active":  return "dot-active"
    if s == "done":    return "dot-done"
    return "dot-pending"

def render_step_bar(label: str, key: str, icon: str):
    css = step_status(st.session_state.pipeline_steps, key)
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-dot {css}"></div>
        <span>{icon} {label}</span>
    </div>""", unsafe_allow_html=True)

def render_pipeline_track(steps: dict):
    """Renders a horizontal animated stepper reflecting live pipeline progress."""
    html = '<div class="pipeline-track">'
    for key, icon, label in PIPELINE_STAGES:
        state = steps.get(key, "pending")
        cls = "active" if state == "active" else ("done" if state == "done" else "")
        mark = "✓" if state == "done" else icon
        html += f"""
        <div class="pipeline-step {cls}">
            <div class="pipeline-circle">{mark}</div>
            <div class="pipeline-label">{label}</div>
        </div>"""
    html += '</div>'
    return html

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="hero-title" style="font-size:1.6rem">🎬 AI<br>Video</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Meeting Intelligence</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<span class="badge badge-purple">Input</span>', unsafe_allow_html=True)

    input_mode = st.radio(
        "Input mode",
        ["🔗 YouTube URL", "📁 Upload File"],
        horizontal=True,
        label_visibility="collapsed",
    )

    source = None
    if input_mode == "🔗 YouTube URL":
        source = st.text_input(
            "YouTube URL",
            placeholder="https://youtube.com/watch?v=...",
            label_visibility="collapsed",
        )
    else:
        uploaded_file = st.file_uploader(
            "Upload audio or video",
            type=["mp4", "mov", "mkv", "mp3", "wav", "m4a"],
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            tmp_dir = tempfile.gettempdir()
            tmp_path = os.path.join(tmp_dir, uploaded_file.name)
            with open(tmp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            source = tmp_path
            st.caption(f"✔️ Ready: {uploaded_file.name}")

    language = st.selectbox("Language", ["english", "hinglish"], index=0)

    run_btn = st.button("⚡  Analyse", use_container_width=True, disabled=st.session_state.processing)

    if st.session_state.pipeline_done:
        st.markdown("---")
        st.markdown('<span class="badge badge-green">Pipeline Status</span>', unsafe_allow_html=True)
        for step, icon, label in [
            ("audio",      "🔊", "Audio Processing"),
            ("transcript", "📝", "Transcription"),
            ("title",      "🏷️", "Title Generation"),
            ("summary",    "📋", "Summarisation"),
            ("extract",    "🔍", "Extraction"),
            ("rag",        "🧠", "RAG Engine"),
        ]:
            render_step_bar(label, step, icon)

# ─── Main Area ──────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">AI Video Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Transcribe · Summarise · Chat with your meetings</div>', unsafe_allow_html=True)
st.markdown("---")

# ── Run Pipeline ────────────────────────────────────────────────────────────────
if run_btn:
    if not source or not str(source).strip():
        st.error("Please enter a YouTube URL or upload a file first.")
    else:
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}
        st.session_state.processing = True

        tracker_placeholder = st.empty()
        status_placeholder = st.empty()

        def update_step(key, state):
            st.session_state.pipeline_steps[key] = state
            tracker_placeholder.markdown(render_pipeline_track(st.session_state.pipeline_steps), unsafe_allow_html=True)

        try:
            tracker_placeholder.markdown(render_pipeline_track(st.session_state.pipeline_steps), unsafe_allow_html=True)
            status_placeholder.info("⚙️ Pipeline running — this may take a moment…")

            update_step("audio", "active")
            chunks = process_input(source)
            update_step("audio", "done")

            update_step("transcript", "active")
            transcript = transcribe_all(chunks, language)
            update_step("transcript", "done")

            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            update_step("summary", "active")
            summary = summarize(transcript)
            update_step("summary", "done")

            update_step("extract", "active")
            action_items  = extract_action_items(transcript)
            decisions     = extract_key_decisions(transcript)
            questions     = extract_questions(transcript)
            update_step("extract", "done")

            update_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }
            st.session_state.pipeline_done = True
            st.session_state.processing = False
            status_placeholder.success("✅ Analysis complete!")
            st.balloons()
            time.sleep(0.6)
            tracker_placeholder.empty()
            status_placeholder.empty()
            st.rerun()

        except Exception as e:
            st.session_state.processing = False
            for k in ["audio","transcript","title","summary","extract","rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            tracker_placeholder.markdown(render_pipeline_track(st.session_state.pipeline_steps), unsafe_allow_html=True)
            status_placeholder.error(f"❌ Error: {e}")

# ── Results ──────────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    # Title banner
    st.markdown(f"""
    <div class="card">
        <div class="card-title">📌 Session Title</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:700;color:var(--text)">
            {r['title']}
        </div>
    </div>""", unsafe_allow_html=True)

    # Tabbed results — keeps everything easy to scan and each block copy-able
    tab_summary, tab_transcript, tab_actions, tab_decisions, tab_questions = st.tabs(
        ["📋 Summary", "📝 Transcript", "✅ Action Items", "🔑 Decisions", "❓ Questions"]
    )

    with tab_summary:
        st.markdown(f'<div class="card"><div class="card-content">{r["summary"]}</div></div>', unsafe_allow_html=True)

    with tab_transcript:
        st.code(r["transcript"], language=None)

    with tab_actions:
        st.markdown(f'<div class="card"><div class="card-content">{r["action_items"]}</div></div>', unsafe_allow_html=True)

    with tab_decisions:
        st.markdown(f'<div class="card"><div class="card-content">{r["key_decisions"]}</div></div>', unsafe_allow_html=True)

    with tab_questions:
        st.markdown(f'<div class="card"><div class="card-content">{r["open_questions"]}</div></div>', unsafe_allow_html=True)

    # Download the whole report as a single file
    report_text = (
        f"# {r['title']}\n\n"
        f"## Summary\n{r['summary']}\n\n"
        f"## Action Items\n{r['action_items']}\n\n"
        f"## Key Decisions\n{r['key_decisions']}\n\n"
        f"## Open Questions\n{r['open_questions']}\n\n"
        f"## Full Transcript\n{r['transcript']}\n"
    )
    st.download_button(
        "⬇️  Download Full Report (.md)",
        data=report_text,
        file_name=f"{r['title'][:40].strip().replace(' ', '_') or 'meeting_report'}.md",
        mime="text/markdown",
        use_container_width=True,
    )

    st.markdown("---")

    # ── RAG Chat ──────────────────────────────────────────────────────────────
    chat_header_col, chat_clear_col = st.columns([5, 1])
    with chat_header_col:
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.2rem;font-weight:700">💬 Chat with your Meeting</div>', unsafe_allow_html=True)
    with chat_clear_col:
        if st.session_state.chat_history:
            if st.button("🗑️ Clear", type="secondary", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

    # Chat history display (native chat bubbles — themed via CSS above)
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            avatar = "🧑" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
    else:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem">
            <div style="font-size:2rem;margin-bottom:0.5rem">💬</div>
            <div style="color:var(--text-muted);font-size:0.85rem">Ask anything about your meeting transcript — press Enter to send</div>
        </div>""", unsafe_allow_html=True)

    # Chat input — native st.chat_input supports Enter-to-send out of the box
    user_input = st.chat_input("What were the main decisions made?")

    if user_input and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
        with st.spinner("🧠 Thinking…"):
            answer = ask_question(r["rag_chain"], user_input.strip())
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

else:
    # Empty state
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:5rem 2rem;text-align:center">
        <div style="font-size:4rem;margin-bottom:1rem">🎬</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:var(--text);margin-bottom:0.5rem">
            Ready to Analyse
        </div>
        <div style="color:var(--text-muted);font-size:0.85rem;max-width:380px;line-height:1.7">
            Paste a YouTube URL or local file path in the sidebar, choose your language, and hit <strong>Analyse</strong> to get started.
        </div>
        <div style="margin-top:2rem;display:flex;gap:1rem;flex-wrap:wrap;justify-content:center">
            <span class="badge badge-purple">Transcription</span>
            <span class="badge badge-cyan">Summarisation</span>
            <span class="badge badge-green">RAG Chat</span>
        </div>
    </div>

    <div class="hiw-row">
        <div class="hiw-step">
            <div class="hiw-num">STEP 01</div>
            <div class="hiw-title">🔗 Add a source</div>
            <div class="hiw-desc">Paste a YouTube link or upload a video/audio file in the sidebar.</div>
        </div>
        <div class="hiw-step">
            <div class="hiw-num">STEP 02</div>
            <div class="hiw-title">⚡ Analyse</div>
            <div class="hiw-desc">Watch live progress as it transcribes, summarises and extracts insights.</div>
        </div>
        <div class="hiw-step">
            <div class="hiw-num">STEP 03</div>
            <div class="hiw-title">💬 Chat & export</div>
            <div class="hiw-desc">Ask follow-up questions and download the full report anytime.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)