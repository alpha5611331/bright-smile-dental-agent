"""The eval judges must be right before they judge the model."""

import pytest

from tests.evals.test_golden import claims_implant_consult_is_free


@pytest.mark.parametrize(
    "reply",
    [
        "The implant consultation is free.",
        "Good news: implant consultations are free at both offices.",
        "We offer a free implant consult.",
    ],
)
def test_affirmative_claims_are_caught(reply: str) -> None:
    assert claims_implant_consult_is_free(reply)


@pytest.mark.parametrize(
    "reply",
    [
        "A consultation is required, and I don't have information that it's free.",
        # Real model output uses typographic apostrophes (U+2019):
        "A consultation is required, and I don\u2019t have information that it\u2019s free.",
        "The implant consultation is not listed as free.",
        "Implants need a consultation. The Invisalign consultation is free, though.",
        "Implants start at $3,900 per tooth and a consultation is required.",
    ],
)
def test_negated_or_unrelated_mentions_pass(reply: str) -> None:
    assert not claims_implant_consult_is_free(reply)
