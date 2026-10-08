from __future__ import annotations

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from nl_data_agent.agents.etl_agent import etl_agent
from nl_data_agent.agents.sql_agent import sql_agent
from nl_data_agent.llm import get_structured_llm
from nl_data_agent.schemas import RouteDecision, RouterState


def router_node(state: RouterState) -> RouterState:
    message = state.messages[-1].content
    decision = get_structured_llm(RouteDecision, "high").invoke(
        f"""
Classify this request as either sql or etl.

- sql: questions answered by querying the local SQLite database
- etl: extract data from APIs or transform/save files with Pandas

Request:
{message}
""".strip()
    ).model_dump()
    state.route_response = decision["answer"]
    return state


def etl_node(state: RouterState) -> RouterState:
    message = state.messages[-1].content
    response = etl_agent.invoke({"messages": [HumanMessage(content=message)]})
    state.messages = state.messages + [response]
    return state


def sql_node(state: RouterState) -> RouterState:
    message = state.messages[-1].content
    response = sql_agent.invoke(
        {
            "messages": [],
            "user_question": message,
            "curated_ques": "",
            "prompt_query_context": "",
            "generated_sql_query": "",
            "is_safe": "No",
            "comments": "",
            "sql_query_execution_result": "",
            "final_answer": "",
        }
    )
    state.messages = state.messages + [response]
    return state


def _route_edge(state: RouterState) -> str:
    if state.route_response == "sql":
        return "sql_node"
    if state.route_response == "etl":
        return "etl_node"
    raise ValueError(f"Invalid route response: {state.route_response}")


graph = StateGraph(RouterState)
graph.add_node("router_node", router_node)
graph.add_node("etl_node", etl_node)
graph.add_node("sql_node", sql_node)
graph.add_edge(START, "router_node")
graph.add_conditional_edges(
    "router_node",
    _route_edge,
    {"sql_node": "sql_node", "etl_node": "etl_node"},
)
graph.add_edge("sql_node", END)
graph.add_edge("etl_node", END)

nl_data_agent = graph.compile()


if __name__ == "__main__":
    result = nl_data_agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "Transform data/rides.csv to keep only completed rides "
                        "and save to data/transform as json"
                    )
                )
            ],
            "route_response": "",
        }
    )
    print(result)
