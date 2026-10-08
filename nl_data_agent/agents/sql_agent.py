from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from nl_data_agent.db.sqlite_store import SqliteStore
from nl_data_agent.llm import get_llm, get_structured_llm
from nl_data_agent.schemas import SafetyJudgment, SqlAgentState


def curate_question(state: SqlAgentState) -> SqlAgentState:
    llm = get_llm("low")
    response = llm.invoke(
        "Rewrite the user's data question as ONE clear question. "
        "Return only that single rewritten question — no options, bullets, or commentary.\n\n"
        f"User question: {state.user_question}"
    ).content.strip()
    state.curated_ques = response
    state.messages = state.messages + [HumanMessage(content=response)]
    return state


def build_sql_prompt(state: SqlAgentState) -> SqlAgentState:
    store = SqliteStore()
    schema_info = store.schema_context()

    state.prompt_query_context = f"""
You convert natural language into a SQLite SQL query.

Rules:
- Output only executable SQLite SQL (no markdown fences, no commentary).
- Use only the tables and columns in the schema below.
- Prefer SELECT / WITH queries. Do not modify data or schema.
- Unless the user asks for a specific row count, add LIMIT 10.

User question:
{state.curated_ques}

Schema:
{schema_info}
""".strip()
    return state


def generate_sql(state: SqlAgentState) -> SqlAgentState:
    llm = get_llm("medium")
    state.generated_sql_query = llm.invoke(state.prompt_query_context).content.strip()
    # Strip accidental markdown fences if the model adds them
    query = state.generated_sql_query
    if query.startswith("```"):
        lines = query.splitlines()
        lines = [line for line in lines if not line.strip().startswith("```")]
        state.generated_sql_query = "\n".join(lines).strip()
    return state


def judge_sql_safety(state: SqlAgentState) -> SqlAgentState:
    llm = get_structured_llm(SafetyJudgment, "medium")
    prompt = f"""
You are a SQL safety judge. Allow only read-only queries (SELECT / WITH).
Reject anything that can change data or schema
(INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, REPLACE, ATTACH, etc.).

Respond Yes if safe, otherwise No, with a short comment.

SQL:
{state.generated_sql_query}
""".strip()
    result = llm.invoke(prompt).model_dump()
    state.is_safe = result["answer"]
    state.comments = result["comments"]
    return state


def cancel_unsafe_sql(state: SqlAgentState) -> SqlAgentState:
    state.sql_query_execution_result = "Query was not executed."
    state.final_answer = (
        "The generated SQL query was blocked as unsafe. "
        f"Reason: {state.comments}"
    )
    state.messages = state.messages + [AIMessage(content=state.final_answer)]
    return state


def run_sql(state: SqlAgentState) -> SqlAgentState:
    store = SqliteStore()
    result = store.execute(state.generated_sql_query)
    state.sql_query_execution_result = result or "No result returned."
    return state


def answer_from_result(state: SqlAgentState) -> SqlAgentState:
    llm = get_llm("low")
    prompt = f"""
Write a short explanation of what the query result means for the user.
Do not repeat the full table. Do not include SQL. 2-4 sentences max.

Question: {state.curated_ques}
Result:
{state.sql_query_execution_result}
""".strip()
    explanation = llm.invoke(prompt).content.strip()
    state.final_answer = explanation
    state.messages = state.messages + [AIMessage(content=explanation)]
    return state


def _safety_edge(state: SqlAgentState) -> str:
    return "run_sql" if state.is_safe.lower() == "yes" else "cancel_unsafe_sql"


graph = StateGraph(SqlAgentState)
graph.add_node("curate_question", curate_question)
graph.add_node("build_sql_prompt", build_sql_prompt)
graph.add_node("generate_sql", generate_sql)
graph.add_node("judge_sql_safety", judge_sql_safety)
graph.add_node("cancel_unsafe_sql", cancel_unsafe_sql)
graph.add_node("run_sql", run_sql)
graph.add_node("answer_from_result", answer_from_result)

graph.add_edge(START, "curate_question")
graph.add_edge("curate_question", "build_sql_prompt")
graph.add_edge("build_sql_prompt", "generate_sql")
graph.add_edge("generate_sql", "judge_sql_safety")
graph.add_conditional_edges(
    "judge_sql_safety",
    _safety_edge,
    {"run_sql": "run_sql", "cancel_unsafe_sql": "cancel_unsafe_sql"},
)
graph.add_edge("cancel_unsafe_sql", END)
graph.add_edge("run_sql", "answer_from_result")
graph.add_edge("answer_from_result", END)

sql_agent = graph.compile()


if __name__ == "__main__":
    result = sql_agent.invoke(
        {
            "messages": [],
            "user_question": "What payment methods exist in the database?",
            "curated_ques": "",
            "prompt_query_context": "",
            "generated_sql_query": "",
            "is_safe": "No",
            "comments": "",
            "sql_query_execution_result": "",
            "final_answer": "",
        }
    )
    print(result.get("final_answer"))
    print(result.get("generated_sql_query"))
