# RideQuery: NL Data Agent

Natural-language AI agent for rideshare analytics. Routes each request to either a **SQL** workflow (SQLite) or an **ETL** workflow (API extract / Pandas transform).

**Author:** Shashank Nampalli

## The problem

You’ve got rideshare data — trips, drivers, fares, ratings — but getting answers still feels like work. Someone has to remember table names, write SQL, or ping an analyst. Pulling data from an API or cleaning a CSV is another rabbit hole entirely. By the time you’ve switched tools, the question you cared about has gone cold.

## How RideQuery solves it

Just ask. Type something like “who are the top-rated drivers?” and RideQuery figures out whether that’s a database question or a data-prep job. For analytics, it writes the SQL for you, blocks anything dangerous, runs it, and shows you the rows plus a plain-English explanation. For ETL, it can fetch an API or reshape a file without you opening a notebook. Same chat either way — talk to your data instead of wrestling it.

## Technical architecture

Under the hood, RideQuery is a small crew of agents wired together with LangGraph, talking to DeepSeek for language understanding. A router listens to your prompt and sends it down the SQL path or the ETL path. The SQL path walks a clear pipeline: tidy up the question, peek at the SQLite schema, generate a query, double-check it’s read-only, run it, then explain the result. The ETL path is a back-and-forth between the model and tools that extract or transform files. Streamlit is the front door; the sample rideshare database lives in SQLite and is loaded from the CSVs in `data/`.

## Features

- Intent routing (`sql` vs `etl`) with LangGraph
- SQLite analyst: clarify question → schema context → SQL → safety check → answer
- ETL agent: extract API JSON or transform local files with generated Pandas code
- DeepSeek chat models via the OpenAI-compatible API
- Streamlit UI with Generated SQL / Result / Explanation sections

## Requirements

- Python 3.12+
- A [DeepSeek](https://platform.deepseek.com/) API key

## Setup

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -e .
```

### API key (pick one — no need to commit secrets)

**Option A — `.env` (local)**

Copy `.env.example` to `.env`:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
SQLITE_DB_PATH=data/nl_data_agent.db
```

**Option B — Streamlit secrets (local or Cloud, no `.env`)**

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, or on
[Streamlit Community Cloud](https://streamlit.io/cloud) open **Settings → Secrets** and paste:

```toml
DEEPSEEK_API_KEY = "sk-your_deepseek_api_key"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
SQLITE_DB_PATH = "data/nl_data_agent.db"
```

**Option C — shell env var**

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."
streamlit run app.py
```

Load the sample rideshare dataset into SQLite:

```bash
python -m nl_data_agent.db.seed
```

## Usage

### Streamlit chat UI

```bash
pip install streamlit
streamlit run app.py
```

Opens a rideshare-themed chat app that routes questions to SQL (SQLite) or ETL.
On Streamlit Cloud, the `.db` file is not in git — the app auto-seeds SQLite from
`data/*.csv` on first run.

### CLI

```bash
python main.py "Show me the top 5 drivers by average rating"
python main.py "Transform data/rides.csv to keep only completed rides and save to data/transform as json"
```

Or from Python:

```python
from langchain_core.messages import HumanMessage
from nl_data_agent.agents.router import nl_data_agent

result = nl_data_agent.invoke({
    "messages": [HumanMessage(content="What payment methods exist?")],
    "route_response": "",
})
print(result)
```

## Project layout

```
nl_data_agent/
  agents/          # router, SQL agent, ETL agent
  db/              # SQLite store + seed script
  tools/           # ETL helpers
  llm.py           # DeepSeek client
  schemas.py       # Pydantic state models
main.py
app.py             # Streamlit chat UI
data/              # sample CSVs, extract/, transform/, SQLite file
```

## Sample data

CSV files under `data/` (users, vehicles, rides, payments, ratings) seed `data/nl_data_agent.db` for SQL demos.
