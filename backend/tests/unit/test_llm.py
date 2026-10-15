from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from bright_smile.agent.llm import MAX_OUTPUT_TOKENS, create_chat_model
from bright_smile.core.config import ReasoningEffort
from tests.factories import make_settings


def test_chat_model_uses_the_responses_api_with_reasoning() -> None:
    """Tools plus reasoning only work on the Responses API (issue #21); keep this pinned."""
    model = create_chat_model(
        make_settings(openai_api_key=SecretStr("sk-test"), openai_model="gpt-5.4-mini")
    )

    assert isinstance(model, ChatOpenAI)
    assert model.use_responses_api is True
    assert model.reasoning_effort == ReasoningEffort.LOW.value
    assert model.model_name == "gpt-5.4-mini"
    assert model.max_tokens == MAX_OUTPUT_TOKENS
    assert model.streaming is True


def test_reasoning_can_be_disabled_for_non_reasoning_models() -> None:
    model = create_chat_model(make_settings(openai_reasoning_effort=None))

    assert isinstance(model, ChatOpenAI)
    assert model.reasoning_effort is None
