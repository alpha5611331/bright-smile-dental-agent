"""Conversation safety flags (SPEC sections 4.3, 4.4)."""

from enum import StrEnum


class Flag(StrEnum):
    EMERGENCY = "emergency"
    MEDICAL_QUESTION = "medical_question"
