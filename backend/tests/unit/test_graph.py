from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage

from bright_smile.agent.graph import AgentState, build_agent
from bright_smile.agent.prompts import build_system_prompt
from bright_smile.domain.flags import Flag
from tests.fakes import ScriptedChatModel


def make_state(*messages: AnyMessage) -> AgentState:
    return {"messages": list(messages), "flags": []}


async def test_agent_replies_and_reports_no_flags_for_ordinary_questions() -> None:
    model = ScriptedChatModel(replies=["Yes, Cigna DPPO is in network."])
    agent = build_agent(model)

    result = await agent.ainvoke(make_state(HumanMessage("Do you take Cigna?")))

    assert result["flags"] == []
    assert isinstance(result["messages"][-1], AIMessage)
    assert result["messages"][-1].text == "Yes, Cigna DPPO is in network."


async def test_prompt_has_static_system_prefix_then_history() -> None:
    model = ScriptedChatModel(replies=["Sure."])
    agent = build_agent(model)
    history: list[AnyMessage] = [HumanMessage("Hi"), AIMessage("Hello! How can I help?")]

    await agent.ainvoke(make_state(*history, HumanMessage("Where are you?")))

    prompt = model.calls[0]
    assert isinstance(prompt[0], SystemMessage)
    assert prompt[0].text == build_system_prompt(lead_capture_enabled=False)
    assert [m.text for m in prompt[1:]] == ["Hi", "Hello! How can I help?", "Where are you?"]


async def test_guard_instructions_sit_right_before_the_latest_user_message() -> None:
    model = ScriptedChatModel(replies=["Please go to the nearest emergency room."])
    agent = build_agent(model)
    history: list[AnyMessage] = [HumanMessage("Hi"), AIMessage("Hello!")]
    urgent = HumanMessage("My face is badly swollen and I can't swallow")

    result = await agent.ainvoke(make_state(*history, urgent))

    assert result["flags"] == [Flag.EMERGENCY]
    prompt = model.calls[0]
    assert prompt[1:3] == history  # cacheable prefix is undisturbed
    assert isinstance(prompt[-2], SystemMessage)
    assert prompt[-2].text.startswith("SAFETY CHECK")
    assert prompt[-1] == urgent
