from bright_smile.agent.kb import render_kb
from bright_smile.agent.prompts import build_system_prompt

EM_DASH = chr(0x2014)


def test_prompt_starts_with_the_knowledge_base_for_a_stable_cached_prefix() -> None:
    prompt = build_system_prompt(lead_capture_enabled=False)

    assert prompt.startswith(render_kb())


def test_prompt_is_identical_across_calls() -> None:
    assert build_system_prompt(lead_capture_enabled=True) == build_system_prompt(
        lead_capture_enabled=True
    )


def test_prompt_covers_the_spec_rules() -> None:
    prompt = build_system_prompt(lead_capture_enabled=True)

    for required in (
        "ONLY source of facts",
        "Never state either time range as fact",
        "Do not diagnose",
        "nearest emergency room",
        "existing patients only",
        "Do NOT say the implant consultation is free",
        "Never claim to be human",
        "Never use em-dashes",
    ):
        assert required in prompt
    assert EM_DASH not in prompt


def test_booking_section_depends_on_tool_availability() -> None:
    with_tool = build_system_prompt(lead_capture_enabled=True)
    without_tool = build_system_prompt(lead_capture_enabled=False)

    assert "`capture_lead`" in with_tool
    assert "`capture_lead`" not in without_tool
    assert "cannot book appointments in this chat yet" in without_tool
