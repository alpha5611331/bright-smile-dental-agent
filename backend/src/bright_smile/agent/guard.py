"""Deterministic safety guard (SPEC sections 4.3, 4.4, 5.2).

The guard flags messages that look like an emergency or a medical question. It never replaces the
assistant's reply: it adds a required instruction for this turn, so a false positive only produces
extra safety guidance.
"""

import re

from bright_smile.agent.kb import KB
from bright_smile.domain.flags import Flag

_EMERGENCY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(severe(ly)?|bad(ly)?|really|very|face|jaw|cheek|eye|neck)\b.{0,30}\b(swell|swollen)",
        r"\b(swell(ing|ed|en)?|swollen)\b.{0,30}\b(severe|spreading|face|jaw|eye|neck|breath|swallow)",
        r"\bbleed(ing|s)?\b.{0,40}\b(won'?t|will not|doesn'?t|does not|can'?t|cannot)\s+stop",
        r"\b(uncontrolled|heavy|nonstop|non-stop)\s+bleed",
        r"\b(trauma|accident|injur(y|ed|ies)|hit (in|on) the (face|mouth|jaw))\b",
        r"\b(knocked|broke|broken|cracked)\b.{0,20}\b(out|tooth|teeth|jaw)\b",
        r"\b(can'?t|cannot|trouble|difficulty)\s+(breath|swallow)",
        r"\bemergency\b",
    )
)

_MEDICAL_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(tooth|teeth|gum|jaw|mouth)?\s*(pain|ache|aching|hurts?|hurting|throbbing|sore)\b",
        r"\btoothache\b",
        r"\b(infection|infected|abscess|pus|fever|sensitiv(e|ity)|numb(ness)?)\b",
        r"\b(ibuprofen|advil|motrin|tylenol|acetaminophen|aspirin|antibiotics?|amoxicillin|"
        r"painkillers?|medication|medicine|dosage|dose|prescription)\b",
        r"\b(should|can|could) i (take|use|apply|rinse)\b",
        r"\bis (it|this|that) (normal|serious|infected|bad|dangerous)\b",
        r"\bsymptoms?\b",
        r"\bloose (tooth|teeth|filling|crown)\b",
        r"\bshould i be (worried|concerned)\b",
    )
)

# Milder versions of the emergency symptoms (gums that bleed when brushing). They count as a
# medical question only when the message is not already an emergency, which has its own guidance.
_MILD_SYMPTOM_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE) for p in (r"\b(bleed(s|ing)?|bled|swollen|swelling)\b",)
)


def detect_flags(text: str) -> frozenset[Flag]:
    """Return the safety flags raised by a user message. Pure and deterministic."""
    flags: set[Flag] = set()
    if any(p.search(text) for p in _EMERGENCY_PATTERNS):
        flags.add(Flag.EMERGENCY)
    if any(p.search(text) for p in _MEDICAL_PATTERNS) or (
        Flag.EMERGENCY not in flags and any(p.search(text) for p in _MILD_SYMPTOM_PATTERNS)
    ):
        flags.add(Flag.MEDICAL_QUESTION)
    return frozenset(flags)


_INSTRUCTIONS: dict[Flag, str] = {
    Flag.EMERGENCY: (
        "SAFETY CHECK: The latest message may describe a dental emergency. Start your reply with "
        "the emergency guidance: for severe swelling, uncontrolled bleeding, or trauma, go to the "
        "nearest emergency room (call 911 if it may be life-threatening). During office hours they "
        f"can call {KB.phone} for a same-day visit when possible; after hours, existing patients "
        f"can call {KB.phone} for the on-call dentist. Then offer further help. Give no treatment "
        "or medication advice."
    ),
    Flag.MEDICAL_QUESTION: (
        "SAFETY CHECK: The latest message may ask for medical, symptom, or medication advice. Do "
        "not diagnose or advise on treatment or medication. Kindly say you can't give medical "
        f"advice and ask them to call the office at {KB.phone}."
    ),
}


def guard_instructions(flags: frozenset[Flag]) -> list[str]:
    """Instructions to add for this turn, in a stable order (emergency first)."""
    return [_INSTRUCTIONS[flag] for flag in Flag if flag in flags]
