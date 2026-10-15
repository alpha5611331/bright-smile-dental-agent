"""Chat model factory (OpenAI via langchain-openai)."""

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from bright_smile.core.config import Settings

# Output cap per model call. Reasoning tokens count toward it, so it leaves headroom above the
# ~120-word replies the prompt asks for (SPEC section 10.2).
MAX_OUTPUT_TOKENS = 1200


def create_chat_model(settings: Settings) -> BaseChatModel:
    # Field names (not the `model`/`api_key`/`timeout` aliases) so the pydantic mypy plugin can
    # type-check the call; ChatOpenAI accepts both.
    return ChatOpenAI(
        model_name=settings.openai_model,
        openai_api_key=settings.openai_api_key,
        max_tokens=MAX_OUTPUT_TOKENS,
        reasoning_effort=(
            settings.openai_reasoning_effort.value if settings.openai_reasoning_effort else None
        ),
        request_timeout=settings.openai_timeout_seconds,
        max_retries=2,
        streaming=True,
        stream_usage=True,
        # Reasoning models reject function tools combined with reasoning_effort on Chat
        # Completions; the Responses API supports both (issue #21).
        use_responses_api=True,
    )
