import pytest

from bright_smile.agent.guard import detect_flags, guard_instructions
from bright_smile.domain.flags import Flag


@pytest.mark.parametrize(
    "message",
    [
        "My jaw is really swollen and the bleeding won't stop",
        "There is severe swelling in my face",
        "I have heavy bleeding after an extraction",
        "I was in an accident and knocked out a tooth",
        "My kid broke a tooth playing hockey",
        "I can't swallow and my cheek is swollen",
        "This is an emergency",
    ],
)
def test_emergencies_are_flagged(message: str) -> None:
    assert Flag.EMERGENCY in detect_flags(message)


@pytest.mark.parametrize(
    "message",
    [
        "Can I take ibuprofen for a toothache?",
        "My tooth hurts when I drink cold water",
        "Is it normal for my gums to be sore?",
        "What dosage of amoxicillin should I use?",
        "I think I have an infection",
    ],
)
def test_medical_questions_are_flagged(message: str) -> None:
    assert Flag.MEDICAL_QUESTION in detect_flags(message)


@pytest.mark.parametrize(
    "message",
    [
        "How much is Invisalign?",
        "Do you take Cigna?",
        "What are your Saturday hours?",
        "Is the Rockville office open on Friday?",
        "I'd like to book a cleaning",
        "Is teeth whitening painless?",
    ],
)
def test_ordinary_questions_are_not_flagged(message: str) -> None:
    assert detect_flags(message) == frozenset()


def test_instructions_are_ordered_emergency_first() -> None:
    instructions = guard_instructions(frozenset({Flag.MEDICAL_QUESTION, Flag.EMERGENCY}))

    assert len(instructions) == 2
    assert "emergency" in instructions[0].lower()
    assert "medical" in instructions[1].lower()


def test_no_instructions_without_flags() -> None:
    assert guard_instructions(frozenset()) == []
