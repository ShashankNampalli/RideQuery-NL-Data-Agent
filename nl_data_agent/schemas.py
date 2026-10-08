from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SqlAgentState(BaseModel):
    messages: list = Field(
        default_factory=list,
        description="Conversation messages for the SQL agent",
    )
    user_question: str = Field(..., description="Original natural-language question")
    curated_ques: str = Field(default="", description="Clarified user question")
    prompt_query_context: str = Field(
        default="", description="Prompt containing schema context for SQL generation"
    )
    generated_sql_query: str = Field(default="", description="Generated SQLite query")
    is_safe: Literal["Yes", "No"] = Field(
        default="No", description="Whether the query is safe to run"
    )
    comments: str = Field(default="", description="Safety judge rationale")
    sql_query_execution_result: str = Field(
        default="", description="Query result rows shown under Answer → Result"
    )
    final_answer: str = Field(
        default="", description="Natural-language explanation under Answer → Explanation"
    )


class SafetyJudgment(BaseModel):
    answer: Literal["Yes", "No"] = Field(
        ..., description="Yes if the SQL is read-only and safe"
    )
    comments: str = Field(..., description="Why the query is safe or unsafe")


class EtlAgentState(BaseModel):
    messages: list = Field(
        default_factory=list,
        description="Conversation messages for the ETL agent",
    )


class RouteDecision(BaseModel):
    answer: Literal["sql", "etl"] = Field(
        ..., description="Whether the request is a SQL or ETL task"
    )
    comments: str = Field(..., description="Short rationale for the routing choice")


class RouterState(BaseModel):
    messages: list = Field(
        default_factory=list,
        description="Conversation messages for the router",
    )
    route_response: str = Field(
        default="", description="Chosen route: sql or etl"
    )
