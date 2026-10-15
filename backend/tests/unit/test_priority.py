import pytest

from bright_smile.domain.leads import Interest, PatientType, Priority, compute_priority


@pytest.mark.parametrize(
    ("interest", "patient_type", "emergency_flagged", "expected"),
    [
        # P1: emergency flag or emergency interest wins over everything.
        (Interest.INVISALIGN, PatientType.NEW, True, Priority.P1),
        (Interest.EMERGENCY, PatientType.EXISTING, False, Priority.P1),
        # P2: high-value treatment.
        (Interest.INVISALIGN, PatientType.EXISTING, False, Priority.P2),
        (Interest.IMPLANT, PatientType.UNKNOWN, False, Priority.P2),
        (Interest.CROWN, PatientType.NEW, False, Priority.P2),
        # P3: new patients.
        (Interest.CLEANING, PatientType.NEW, False, Priority.P3),
        (Interest.NEW_PATIENT_EXAM, PatientType.UNKNOWN, False, Priority.P3),
        # P4: everything else.
        (Interest.CLEANING, PatientType.EXISTING, False, Priority.P4),
        (Interest.WHITENING, PatientType.UNKNOWN, False, Priority.P4),
        (Interest.INSURANCE_QUESTION, PatientType.EXISTING, False, Priority.P4),
    ],
)
def test_priority_rules(
    interest: Interest, patient_type: PatientType, emergency_flagged: bool, expected: Priority
) -> None:
    assert (
        compute_priority(
            interest=interest, patient_type=patient_type, emergency_flagged=emergency_flagged
        )
        is expected
    )


def test_priority_values_sort_in_callback_order() -> None:
    assert sorted(Priority, key=str) == [Priority.P1, Priority.P2, Priority.P3, Priority.P4]
