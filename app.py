from __future__ import annotations

import html
import sqlite3
from typing import Any

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from nl_data_agent.agents.router import nl_data_agent
from nl_data_agent.paths import default_db_path, project_root

st.set_page_config(
    page_title="RideQuery: NL Data Agent",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "RideQuery"
APP_TAGLINE = "NL Data Agent"
AUTHOR_NAME = "Shashank Nampalli"

SAMPLE_PROMPTS = [
    "Show me the top 5 drivers by average rating",
    "What payment methods do we have and how many payments use each?",
    "Average fare and distance for completed rides",
    "How many active drivers are in each city?",
    "Transform data/rides.csv to keep only completed rides and save to data/transform as json",
    "From data/ratings.csv, compute average rating per driver_id and save to data/transform as csv",
    "Filter data/payments.csv to completed credit_card payments and save as parquet in data/transform",
]


def inject_styles() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Figtree:wght@400;500;600&display=swap');

:root {
  --ink: #14181f;
  --muted: #5c6675;
  --fog: #edf1f5;
  --surface: #f8fafb;
  --line: #c9d2dc;
  --signal: #ef9b0f;
  --signal-deep: #c77800;
  --route: #0f8a74;
  --asphalt: #1c232e;
}

html, body, [class*="css"] {
  font-family: "Figtree", sans-serif;
  color: var(--ink);
}

.stApp {
  background:
    radial-gradient(1200px 500px at 12% -10%, rgba(239, 155, 15, 0.18), transparent 55%),
    radial-gradient(900px 420px at 100% 0%, rgba(15, 138, 116, 0.12), transparent 50%),
    linear-gradient(180deg, #f4f7fa 0%, #e9eef3 100%);
}

.stApp::before {
  content: "";
  pointer-events: none;
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(20, 24, 31, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(20, 24, 31, 0.035) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(180deg, rgba(0,0,0,0.55), transparent 70%);
  z-index: 0;
}

[data-testid="stAppViewContainer"] > .main {
  position: relative;
  z-index: 1;
}

/* Do not hide footer — Streamlit mounts st.chat_input there. */
#MainMenu { visibility: hidden; }
header a[href*="streamlit.io"],
footer a[href*="streamlit.io"] {
  display: none !important;
}

.hero {
  position: relative;
  overflow: hidden;
  border-radius: 28px;
  padding: 2.2rem 2.2rem 1.8rem;
  margin-bottom: 1.25rem;
  color: #f7f8fa;
  background:
    linear-gradient(135deg, rgba(28, 35, 46, 0.96), rgba(20, 24, 31, 0.92)),
    radial-gradient(600px 240px at 85% 20%, rgba(239, 155, 15, 0.35), transparent 60%);
  box-shadow: 0 24px 60px rgba(20, 24, 31, 0.18);
}

.hero-brand {
  font-family: "Syne", sans-serif;
  font-weight: 800;
  font-size: clamp(2.4rem, 5vw, 3.6rem);
  letter-spacing: -0.04em;
  line-height: 0.95;
  margin: 0 0 0.7rem 0;
}

.hero-brand span {
  color: var(--signal);
}

.hero-tag {
  display: inline-block;
  margin: 0 0 0.75rem 0;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: rgba(247, 248, 250, 0.9);
  background: rgba(239, 155, 15, 0.18);
  border: 1px solid rgba(239, 155, 15, 0.35);
}

.hero-copy {
  max-width: 34rem;
  margin: 0;
  font-size: 1.05rem;
  color: rgba(247, 248, 250, 0.78);
  line-height: 1.45;
}

.route-svg {
  position: absolute;
  right: -1rem;
  top: 0.5rem;
  width: min(42vw, 360px);
  opacity: 0.9;
}

.pulse {
  animation: pulse 2.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.55; r: 5; }
  50% { opacity: 1; r: 7; }
}

.dash {
  stroke-dasharray: 10 12;
  animation: dash 18s linear infinite;
}

@keyframes dash {
  to { stroke-dashoffset: -240; }
}

.badge-row {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
  margin-top: 1.15rem;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  background: rgba(247, 248, 250, 0.08);
  border: 1px solid rgba(247, 248, 250, 0.14);
  color: rgba(247, 248, 250, 0.88);
}

.badge .dot {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  background: var(--signal);
  box-shadow: 0 0 0 4px rgba(239, 155, 15, 0.18);
}

.panel {
  background: rgba(248, 250, 251, 0.86);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1rem 1.1rem;
  margin-bottom: 0.85rem;
}

.panel h3 {
  font-family: "Syne", sans-serif;
  font-size: 0.95rem;
  margin: 0 0 0.55rem 0;
  letter-spacing: -0.02em;
}

.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.55rem;
}

.stat {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.7rem 0.8rem;
}

.stat .label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
}

.stat .value {
  font-family: "Syne", sans-serif;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.1;
  margin-top: 0.15rem;
}

.route-chip {
  display: inline-block;
  margin-bottom: 0.45rem;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.route-chip.sql {
  background: rgba(15, 138, 116, 0.12);
  color: var(--route);
}

.route-chip.etl {
  background: rgba(239, 155, 15, 0.16);
  color: var(--signal-deep);
}

.response-stack {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  margin-top: 0.35rem;
}

.response-section {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 0.95rem 1.05rem;
}

.response-section h4 {
  font-family: "Syne", sans-serif;
  font-size: 0.95rem;
  font-weight: 700;
  margin: 0 0 0.65rem 0;
  letter-spacing: -0.02em;
  color: var(--ink);
}

.answer-sub {
  margin-top: 0.75rem;
}

.answer-sub:first-of-type {
  margin-top: 0;
}

.answer-sub h5 {
  font-family: "Syne", sans-serif;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
  margin: 0 0 0.4rem 0;
}

.sql-block, .result-block {
  margin: 0;
  padding: 0.75rem 0.85rem;
  border-radius: 12px;
  background: var(--asphalt);
  color: #e8edf3;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.82rem;
  white-space: pre-wrap;
  overflow-x: auto;
}

.result-block {
  background: #243040;
}

.explanation-text {
  margin: 0;
  color: var(--ink);
  line-height: 1.5;
  font-size: 0.98rem;
}

div[data-testid="stChatMessage"] {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(201, 210, 220, 0.7);
  border-radius: 16px;
  padding: 0.35rem 0.5rem;
}

.stButton > button {
  border-radius: 999px !important;
  border: 1px solid var(--line) !important;
  background: #fff !important;
  color: var(--ink) !important;
  font-weight: 600 !important;
}

.stButton > button:hover {
  border-color: var(--signal) !important;
  color: var(--signal-deep) !important;
}

[data-testid="stChatInput"],
[data-testid="stBottomBlockContainer"] {
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 1000 !important;
}

[data-testid="stChatInput"] textarea {
  border-radius: 16px !important;
}

.composer {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 1rem 1.1rem 0.85rem;
  margin: 0 0 1.25rem 0;
  box-shadow: 0 10px 30px rgba(20, 24, 31, 0.06);
}

.composer-title {
  font-family: "Syne", sans-serif;
  font-size: 1rem;
  font-weight: 700;
  margin: 0 0 0.35rem 0;
  letter-spacing: -0.02em;
}

.composer-hint {
  color: var(--muted);
  font-size: 0.86rem;
  margin: 0 0 0.75rem 0;
}

button[kind="primary"],
.stButton > button[kind="primary"],
div[data-testid="stFormSubmitButton"] button {
  background: var(--signal) !important;
  border-color: var(--signal) !important;
  color: #14181f !important;
  font-weight: 700 !important;
}

section[data-testid="stSidebar"] {
  background: rgba(248, 250, 251, 0.92);
  border-right: 1px solid var(--line);
}

.author-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  margin-top: 1rem;
  padding: 0.4rem 0.8rem;
  border-radius: 999px;
  background: rgba(239, 155, 15, 0.14);
  border: 1px solid rgba(239, 155, 15, 0.35);
  color: #f7f8fa;
  font-size: 0.86rem;
  font-weight: 600;
}

.author-chip strong {
  color: var(--signal);
  font-weight: 700;
}

.arch-intro {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1rem 1.15rem;
  margin-bottom: 1rem;
}

.arch-intro h3 {
  font-family: "Syne", sans-serif;
  margin: 0 0 0.4rem 0;
  letter-spacing: -0.02em;
}

.arch-intro p {
  margin: 0;
  color: var(--muted);
  line-height: 1.45;
}

button[data-baseweb="tab"] {
  font-family: "Syne", sans-serif !important;
  font-weight: 700 !important;
}

.dag-board {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1.1rem 1rem 1.25rem;
  margin-bottom: 1rem;
}

.dag-board h4 {
  font-family: "Syne", sans-serif;
  margin: 0 0 0.9rem 0;
  letter-spacing: -0.02em;
}

.dag-row {
  display: flex;
  justify-content: center;
  align-items: stretch;
  flex-wrap: wrap;
  gap: 0.7rem;
  margin: 0.35rem 0;
}

.dag-node {
  min-width: 140px;
  max-width: 220px;
  padding: 0.7rem 0.85rem;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: #fff;
  text-align: center;
  box-shadow: 0 8px 18px rgba(20, 24, 31, 0.05);
}

.dag-node .title {
  font-family: "Syne", sans-serif;
  font-weight: 700;
  font-size: 0.92rem;
  color: var(--ink);
  line-height: 1.2;
}

.dag-node .sub {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--muted);
}

.dag-node.signal {
  background: #fff7e8;
  border-color: rgba(239, 155, 15, 0.45);
}

.dag-node.route {
  background: #e8f7f3;
  border-color: rgba(15, 138, 116, 0.35);
}

.dag-node.asphalt {
  background: #1c232e;
  border-color: #1c232e;
  color: #f7f8fa;
}

.dag-node.asphalt .title { color: #f7f8fa; }
.dag-node.asphalt .sub { color: rgba(247, 248, 250, 0.7); }

.dag-arrow {
  text-align: center;
  color: var(--muted);
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  margin: 0.15rem 0;
}

.dag-label {
  display: inline-block;
  margin: 0 0.25rem;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  background: rgba(20, 24, 31, 0.06);
  color: var(--muted);
}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
<div class="hero">
  <svg class="route-svg" viewBox="0 0 360 180" fill="none" aria-hidden="true">
    <path class="dash" d="M20 140 C70 40, 120 160, 180 70 S280 20, 340 90"
          stroke="#ef9b0f" stroke-width="3" fill="none" stroke-linecap="round"/>
    <circle cx="20" cy="140" r="7" fill="#0f8a74"/>
    <circle class="pulse" cx="340" cy="90" r="6" fill="#ef9b0f"/>
    <circle cx="180" cy="70" r="4" fill="#f7f8fa" opacity="0.7"/>
  </svg>
  <h1 class="hero-brand">Ride<span>Query</span></h1>
  <p class="hero-tag">NL Data Agent</p>
  <p class="hero-copy">
    Ask about rides, drivers, fares, and ratings like you’d ask a teammate —
    or tell it to pull and reshape a file. DeepSeek + SQLite under the hood.
  </p>
  <div class="badge-row">
    <div class="badge"><span class="dot"></span>Rideshare domain</div>
    <div class="badge">SQL · safety-checked</div>
    <div class="badge">ETL · extract &amp; transform</div>
  </div>
  <div class="author-chip">Author · <strong>__AUTHOR__</strong></div>
</div>
        """.replace("__AUTHOR__", html.escape(AUTHOR_NAME)),
        unsafe_allow_html=True,
    )


def _node(title: str, sub: str = "", kind: str = "") -> str:
    cls = f"dag-node {kind}".strip()
    sub_html = f'<div class="sub">{html.escape(sub)}</div>' if sub else ""
    return (
        f'<div class="{cls}">'
        f'<div class="title">{html.escape(title)}</div>'
        f"{sub_html}"
        f"</div>"
    )


def _arrow(label: str = "") -> str:
    if label:
        return (
            f'<div class="dag-arrow">↓ '
            f'<span class="dag-label">{html.escape(label)}</span></div>'
        )
    return '<div class="dag-arrow">↓</div>'


def render_architecture_page() -> None:
    st.markdown(
        f"""
<div class="arch-intro">
  <h3>Tech Architecture</h3>
  <p style="margin-bottom:0.75rem;">
    <strong>The problem.</strong> You’ve got rides, drivers, fares, and ratings sitting in
    tables — but answering a simple question still means writing SQL, remembering schemas,
    or waiting on someone else. Cleaning a file or pulling an API is a totally different
    chore. Too many tools for one honest question.
  </p>
  <p style="margin-bottom:0.75rem;">
    <strong>How we solve it.</strong> {html.escape(APP_NAME)} lets you ask in plain English.
    It decides whether you need analytics or data prep. Analytics path: safe SQL, real rows,
    and a short explanation. ETL path: fetch or reshape data without opening a notebook.
    One chat for both.
  </p>
  <p style="margin-bottom:0.75rem;">
    <strong>How it’s built.</strong> Streamlit is the front door. Behind it, LangGraph runs a
    few cooperating agents on DeepSeek. A router sends your prompt to SQL or ETL. The SQL
    flow cleans up the question, looks at the SQLite schema, writes a query, checks it’s
    read-only, runs it, then explains the answer. The ETL flow chats with tools until the
    extract or transform is done. Sample rideshare data lives in SQLite, loaded from the
    CSVs in <code>data/</code>.
  </p>
  <p style="margin-top:0.65rem;color:#14181f;"><strong>Author:</strong> {html.escape(AUTHOR_NAME)}</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="dag-board">
  <h4>End-to-end DAG</h4>
  <div class="dag-row">{_node("User Prompt", "natural language", "signal")}</div>
  {_arrow()}
  <div class="dag-row">{_node("Streamlit UI", "chat + architecture tabs")}</div>
  {_arrow()}
  <div class="dag-row">{_node("Router Agent", "sql or etl", "route")}</div>
  {_arrow("branches")}
  <div class="dag-row">
    {_node("SQL Agent", "rideshare analytics", "route")}
    {_node("ETL Agent", "extract / transform", "signal")}
  </div>
  {_arrow()}
  <div class="dag-row">
    {_node("Safety Judge", "read-only SQL only")}
    {_node("ETL Tools", "API + Pandas")}
  </div>
  {_arrow()}
  <div class="dag-row">
    {_node("SQLite DB", "rides · drivers · fares", "asphalt")}
    {_node("Files", "data/extract · transform", "asphalt")}
  </div>
  {_arrow()}
  <div class="dag-row">{_node("Answer", "Generated SQL · Result · Explanation", "route")}</div>
  {_arrow("powered by")}
  <div class="dag-row">{_node("DeepSeek LLM", "chat + tool calling", "signal")}</div>
</div>

<div class="dag-board">
  <h4>Router DAG</h4>
  <div class="dag-row">{_node("Start", "", "asphalt")}</div>
  {_arrow()}
  <div class="dag-row">{_node("router_node", "classify intent", "route")}</div>
  {_arrow("sql | etl")}
  <div class="dag-row">
    {_node("sql_node", "SQL subgraph")}
    {_node("etl_node", "ETL subgraph")}
  </div>
  {_arrow()}
  <div class="dag-row">{_node("End", "", "asphalt")}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f"""
<div class="dag-board">
  <h4>SQL Agent DAG</h4>
  <div class="dag-row">{_node("Start", "", "asphalt")}</div>
  {_arrow()}
  <div class="dag-row">{_node("curate_question")}</div>
  {_arrow()}
  <div class="dag-row">{_node("build_sql_prompt")}</div>
  {_arrow()}
  <div class="dag-row">{_node("generate_sql")}</div>
  {_arrow()}
  <div class="dag-row">{_node("judge_sql_safety", "Yes / No", "signal")}</div>
  {_arrow("safe | unsafe")}
  <div class="dag-row">
    {_node("run_sql", "SQLite", "route")}
    {_node("cancel_unsafe_sql")}
  </div>
  {_arrow()}
  <div class="dag-row">{_node("answer_from_result", "Result + Explanation")}</div>
  {_arrow()}
  <div class="dag-row">{_node("End", "", "asphalt")}</div>
</div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            f"""
<div class="dag-board">
  <h4>ETL Agent DAG</h4>
  <div class="dag-row">{_node("Start", "", "asphalt")}</div>
  {_arrow()}
  <div class="dag-row">{_node("llm_node", "plan + tool calls", "signal")}</div>
  {_arrow("tool calls")}
  <div class="dag-row">{_node("tool_node", "extract / transform", "route")}</div>
  {_arrow("loop back")}
  <div class="dag-row">{_node("llm_node", "until done", "signal")}</div>
  {_arrow("done")}
  <div class="dag-row">{_node("End", "", "asphalt")}</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.caption(
        f"{APP_NAME}: {APP_TAGLINE} · Built by {AUTHOR_NAME} · DeepSeek · LangGraph · SQLite · Streamlit"
    )


def db_stats() -> dict[str, int] | None:
    path = default_db_path()
    if not path.exists():
        return None
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        stats = {}
        for table in ("rides", "users", "vehicles", "payments", "ratings"):
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = int(cur.fetchone()[0])
        conn.close()
        return stats
    except Exception:
        return None


def extract_reply(result: dict[str, Any]) -> dict[str, str]:
    """Normalize agent output into display sections."""
    route = str(result.get("route_response") or "")
    sql_query = ""
    query_result = ""
    explanation = "No response generated."

    for item in reversed(result.get("messages") or []):
        if isinstance(item, dict) and (
            "generated_sql_query" in item
            or "sql_query_execution_result" in item
            or "final_answer" in item
        ):
            sql_query = str(item.get("generated_sql_query") or "")
            query_result = str(item.get("sql_query_execution_result") or "")
            explanation = str(item.get("final_answer") or explanation)
            break

        if isinstance(item, dict):
            nested_messages = item.get("messages") or []
            for nested in reversed(nested_messages):
                if isinstance(nested, AIMessage) and nested.content:
                    explanation = str(nested.content)
                    query_result = str(nested.content)
                    break
                if isinstance(nested, dict) and nested.get("content"):
                    explanation = str(nested["content"])
                    query_result = str(nested["content"])
                    break
            else:
                continue
            break

        if isinstance(item, AIMessage) and item.content:
            explanation = str(item.content)
            query_result = str(item.content)
            break

    if route == "etl" and not sql_query:
        sql_query = "Not applicable for ETL requests."
        if not query_result:
            query_result = explanation

    return {
        "route": route,
        "sql": sql_query,
        "result": query_result or "No result returned.",
        "explanation": explanation,
    }


def render_structured_reply(payload: dict[str, str]) -> None:
    route = payload.get("route") or ""
    if route:
        st.markdown(
            f'<span class="route-chip {html.escape(route)}">via {html.escape(route)}</span>',
            unsafe_allow_html=True,
        )

    sql_text = payload.get("sql") or "No SQL generated."
    result_text = payload.get("result") or "No result returned."
    explanation_text = payload.get("explanation") or ""

    st.markdown('<div class="response-stack">', unsafe_allow_html=True)

    st.markdown('<div class="response-section">', unsafe_allow_html=True)
    st.markdown("#### Generated SQL")
    st.code(sql_text, language="sql")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="response-section">', unsafe_allow_html=True)
    st.markdown("#### Answer")
    st.markdown("##### Result")
    # Pipe tables from SQLite render as markdown tables
    if " | " in result_text and "\n" in result_text:
        st.markdown(result_text)
    else:
        st.code(result_text)
    st.markdown("##### Explanation")
    st.markdown(explanation_text)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def run_agent(query: str) -> dict[str, Any]:
    return nl_data_agent.invoke(
        {
            "messages": [HumanMessage(content=query)],
            "route_response": "",
        }
    )


def ensure_session() -> None:
    if "chat" not in st.session_state:
        st.session_state.chat = []


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Dispatch board")
        st.caption("Sample rideshare prompts — click to queue.")

        for prompt in SAMPLE_PROMPTS:
            if st.button(prompt, use_container_width=True, key=f"sample_{hash(prompt)}"):
                st.session_state.pending_prompt = prompt

        stats = db_stats()
        st.markdown("---")
        if stats is None:
            st.warning(
                "SQLite DB not found. Run `python -m nl_data_agent.db.seed` first."
            )
        else:
            st.markdown(
                f"""
<div class="panel">
  <h3>Fleet snapshot</h3>
  <div class="stat-grid">
    <div class="stat"><div class="label">Rides</div><div class="value">{stats['rides']:,}</div></div>
    <div class="stat"><div class="label">Users</div><div class="value">{stats['users']:,}</div></div>
    <div class="stat"><div class="label">Vehicles</div><div class="value">{stats['vehicles']:,}</div></div>
    <div class="stat"><div class="label">Ratings</div><div class="value">{stats['ratings']:,}</div></div>
  </div>
</div>
                """,
                unsafe_allow_html=True,
            )
            db_path = default_db_path()
            try:
                db_label = db_path.relative_to(project_root())
            except ValueError:
                db_label = db_path
            st.caption(f"DB · `{db_label}`")


def render_composer() -> str | None:
    """Visible prompt panel in the main column (always on-screen)."""
    st.markdown(
        """
<div class="composer">
  <p class="composer-title">Ask a question</p>
  <p class="composer-hint">
    Type a rideshare analytics question or an ETL request, then hit Send.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    pending = st.session_state.pop("pending_prompt", None)
    if pending:
        st.session_state["composer_text"] = pending

    with st.form("ask_form", clear_on_submit=True):
        text = st.text_area(
            "Question",
            key="composer_text",
            height=110,
            placeholder="e.g. Show me the top 5 drivers by average rating",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Send", type="primary", use_container_width=True)

    if submitted:
        cleaned = (text or "").strip()
        return cleaned or None
    return None


def append_and_show(prompt: str) -> None:
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Routing across the city…"):
            try:
                result = run_agent(prompt)
                payload = extract_reply(result)
            except Exception as exc:
                payload = {
                    "route": "",
                    "sql": "",
                    "result": "No result returned.",
                    "explanation": f"Something went wrong: {exc}",
                }

        render_structured_reply(payload)

    st.session_state.chat.append({"user": prompt, **payload})


def render_chat_page() -> None:
    prompt = render_composer()

    for turn in st.session_state.chat:
        with st.chat_message("user"):
            st.markdown(turn["user"])
        with st.chat_message("assistant"):
            # Support older chat turns that only stored a flat assistant string
            if "result" in turn or "explanation" in turn or turn.get("sql"):
                render_structured_reply(
                    {
                        "route": turn.get("route") or "",
                        "sql": turn.get("sql") or turn.get("assistant") or "",
                        "result": turn.get("result") or "",
                        "explanation": turn.get("explanation")
                        or turn.get("assistant")
                        or "",
                    }
                )
            else:
                st.markdown(turn.get("assistant") or "")

    # Bottom chat input as a second entry point
    bottom = st.chat_input("Or type here and press Enter…")
    prompt = prompt or bottom

    if prompt:
        append_and_show(prompt)
        st.rerun()


def main() -> None:
    inject_styles()
    ensure_session()
    render_hero()
    render_sidebar()

    tab_chat, tab_arch = st.tabs(["Chat", "Tech Architecture"])
    with tab_chat:
        render_chat_page()
    with tab_arch:
        render_architecture_page()


if __name__ == "__main__":
    main()
