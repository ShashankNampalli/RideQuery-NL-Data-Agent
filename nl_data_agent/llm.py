from __future__ import annotations

from typing import TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from nl_data_agent.config import get_setting

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def get_llm(level: str = "medium") -> ChatOpenAI:
    """
    Return a DeepSeek chat model via the OpenAI-compatible API.

    Levels (low / medium / high / claude) all use deepseek-chat so routing,
    tool calling, and structured output stay on the same capable model.
    """
    api_key = get_setting("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "DEEPSEEK_API_KEY is not set. Use a .env file, environment variable, "
            "or Streamlit secrets (.streamlit/secrets.toml / Cloud Secrets)."
        )

    level_key = level.lower().strip()
    if level_key not in {"low", "medium", "high", "claude"}:
        raise ValueError(f"Unsupported level: {level}")

    base_url = get_setting("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL) or DEFAULT_BASE_URL

    return ChatOpenAI(
        model=DEFAULT_MODEL,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
    )


def get_structured_llm(schema: type[SchemaT], level: str = "medium"):
    """
    Structured output for DeepSeek.

    DeepSeek does not support OpenAI json_schema response_format, so use
    function calling instead of LangChain's default method.
    """
    return get_llm(level).with_structured_output(schema, method="function_calling")
