"""LangGraph agent: `START -> guard -> agent <-> tools -> END` (SPEC section 9.1)."""

from collections.abc import Sequence
from enum import StrEnum
from typing import Annotated, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from bright_smile.agent.guard import detect_flags, guard_instructions
from bright_smile.agent.prompts import build_system_prompt
from bright_smile.domain.flags import Flag


class Node(StrEnum):
    GUARD = "guard"
    AGENT = "agent"
    TOOLS = "tools"


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    flags: list[Flag]


type Agent = CompiledStateGraph[AgentState, None, AgentState, AgentState]


def _latest_user_text(messages: Sequence[AnyMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.text
    return ""


def _with_turn_instructions(
    system_prompt: str, messages: Sequence[AnyMessage], flags: Sequence[Flag]
) -> list[AnyMessage]:
    """Static system prompt first (cacheable prefix), then turn-specific guard instructions."""
    prompt: list[AnyMessage] = [SystemMessage(system_prompt), *messages]
    instructions = guard_instructions(frozenset(flags))
    if instructions:
        last_user = max(i for i, m in enumerate(prompt) if isinstance(m, HumanMessage))
        prompt[last_user:last_user] = [SystemMessage(text) for text in instructions]
    return prompt


def build_agent(model: BaseChatModel, tools: Sequence[BaseTool] = ()) -> Agent:
    """Compile the agent graph. Tools are optional so the graph works before any are registered."""
    system_prompt = build_system_prompt(lead_capture_enabled=bool(tools))
    bound = model.bind_tools(list(tools)) if tools else model

    async def guard(state: AgentState) -> dict[str, list[Flag]]:
        flags = detect_flags(_latest_user_text(state["messages"]))
        return {"flags": [flag for flag in Flag if flag in flags]}

    async def agent(state: AgentState, config: RunnableConfig) -> dict[str, list[AnyMessage]]:
        prompt = _with_turn_instructions(system_prompt, state["messages"], state["flags"])
        response = await bound.ainvoke(prompt, config)
        return {"messages": [response]}

    def route_after_agent(state: AgentState) -> str:
        last = state["messages"][-1]
        if tools and isinstance(last, AIMessage) and last.tool_calls:
            return Node.TOOLS
        return END

    graph = StateGraph(AgentState)
    graph.add_node(Node.GUARD, guard)
    graph.add_node(Node.AGENT, agent)
    graph.add_edge(START, Node.GUARD)
    graph.add_edge(Node.GUARD, Node.AGENT)
    if tools:
        graph.add_node(Node.TOOLS, ToolNode(list(tools)))
        graph.add_conditional_edges(Node.AGENT, route_after_agent, [Node.TOOLS, END])
        graph.add_edge(Node.TOOLS, Node.AGENT)
    else:
        graph.add_edge(Node.AGENT, END)
    return graph.compile()
