from __future__ import annotations

from langchain.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from nl_data_agent.llm import get_llm
from nl_data_agent.schemas import EtlAgentState
from nl_data_agent.tools.etl import EtlToolkit


@tool
def extract_load_tool(url: str, output_folder: str, format: str) -> str:
    """Extract JSON from an HTTP API and save it under the project as csv/json/parquet.

    Args:
        url: API endpoint to fetch.
        output_folder: Project-relative folder (for example data/extract).
        format: Output format — csv, json, or parquet.
    """
    return EtlToolkit().extract_load(url, output_folder, format)


@tool
def transform_load_tool(
    input_file_path: str,
    output_folder: str,
    output_format: str,
    user_question: str,
) -> str:
    """Generate and run Pandas code to transform a local file, then save the result.

    Args:
        input_file_path: Project-relative input file path.
        output_folder: Project-relative output folder (for example data/transform).
        output_format: Desired output format — csv, json, or parquet.
        user_question: Transformation instructions from the user.
    """
    toolkit = EtlToolkit()
    preview = toolkit.preview_file(input_file_path)
    llm = get_llm("high")

    prompt = f"""
You write Pandas-only Python for an ETL step.
Return executable code only — no markdown fences and no commentary.

Requirements:
- Read the data from: {input_file_path}
- Transform it according to: {user_question}
- Save the result under: {output_folder} using format: {output_format}
- Use pandas as pd if needed

Data preview:
{preview}
""".strip()

    response = llm.invoke(prompt).content
    pandas_code = response.strip().strip("`")
    if pandas_code.lower().startswith("python"):
        pandas_code = pandas_code[6:].strip()

    results = toolkit.execute_code(pandas_code)
    return (
        f"Transform finished. Output folder: {output_folder} ({output_format}).\n\n"
        f"Pandas code:\n{pandas_code}\n\nExecution result:\n{results}"
    )


TOOLS = [extract_load_tool, transform_load_tool]


def _tool_llm():
    return get_llm("high").bind_tools(TOOLS)


def llm_node(state: EtlAgentState) -> EtlAgentState:
    messages = state.messages
    prompt = f"""
You are an ETL assistant with tools to extract/load API data and transform/load files.
Use tools when needed. When the work is done, tell the user briefly and stop.

Chat history:
{messages}
""".strip()
    answer = _tool_llm().invoke(prompt)
    state.messages = messages + [answer]
    return state


def tool_node(state: EtlAgentState) -> EtlAgentState:
    tools_by_name = {item.name: item for item in TOOLS}
    tool_calls = state.messages[-1].tool_calls
    results = []
    for call in tool_calls:
        observation = tools_by_name[call["name"]].invoke(call["args"])
        results.append(ToolMessage(content=observation, tool_call_id=call["id"]))
    state.messages = state.messages + results
    return state


def _maybe_use_tools(state: EtlAgentState) -> str:
    return "tool_node" if getattr(state.messages[-1], "tool_calls", None) else "end"


graph = StateGraph(EtlAgentState)
graph.add_node("llm_node", llm_node)
graph.add_node("tool_node", tool_node)
graph.add_edge(START, "llm_node")
graph.add_conditional_edges(
    "llm_node",
    _maybe_use_tools,
    {"tool_node": "tool_node", "end": END},
)
graph.add_edge("tool_node", "llm_node")

etl_agent = graph.compile()


if __name__ == "__main__":
    response = etl_agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "Transform data/rides.csv to keep only completed rides "
                        "and save to data/transform as json"
                    )
                )
            ]
        }
    )
    print(response)
