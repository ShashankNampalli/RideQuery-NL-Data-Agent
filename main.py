from __future__ import annotations

import argparse

from langchain_core.messages import HumanMessage

from nl_data_agent.agents.router import nl_data_agent


def run(query: str) -> dict:
    return nl_data_agent.invoke(
        {
            "messages": [HumanMessage(content=query)],
            "route_response": "",
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="RideQuery: NL Data Agent")
    parser.add_argument(
        "query",
        nargs="?",
        default=(
            "Transform data/rides.csv to keep only completed rides "
            "and save to data/transform as json"
        ),
        help="Natural-language request (SQL or ETL)",
    )
    args = parser.parse_args()
    result = run(args.query)
    print(result)


if __name__ == "__main__":
    main()
