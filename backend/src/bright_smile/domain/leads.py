"""Lead vocabulary and the deterministic priority rule (SPEC sections 6.1, 6.3)."""

from enum import StrEnum


class PreferredLocation(StrEnum):
    BETHESDA = "bethesda"
    ROCKVILLE = "rockville"
    NO_PREFERENCE = "no_preference"


class PatientType(StrEnum):
    NEW = "new"
    EXISTING = "existing"
    UNKNOWN = "unknown"


class Interest(StrEnum):
    NEW_PATIENT_EXAM = "new_patient_exam"
    CLEANING = "cleaning"
    FILLING = "filling"
    CROWN = "crown"
    WHITENING = "whitening"
    INVISALIGN = "invisalign"
    IMPLANT = "implant"
    EMERGENCY = "emergency"
    INSURANCE_QUESTION = "insurance_question"
    OTHER = "other"


class Priority(StrEnum):
    """Callback order: P1 first. String values sort in priority order."""

    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class LeadStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    SCHEDULED = "scheduled"
    NOT_INTERESTED = "not_interested"


class LeadSource(StrEnum):
    CHAT = "chat"
    FORM = "form"


HIGH_VALUE_INTERESTS = frozenset({Interest.INVISALIGN, Interest.IMPLANT, Interest.CROWN})


def compute_priority(
    *, interest: Interest, patient_type: PatientType, emergency_flagged: bool
) -> Priority:
    """First matching rule wins (SPEC section 6.3)."""
    if emergency_flagged or interest is Interest.EMERGENCY:
        return Priority.P1
    if interest in HIGH_VALUE_INTERESTS:
        return Priority.P2
    if patient_type is PatientType.NEW or interest is Interest.NEW_PATIENT_EXAM:
        return Priority.P3
    return Priority.P4
