"""Bright Smile Dental knowledge base: the assistant's only source of facts (SPEC section 4.1).

Transcribed from `context/Bright_Smile_Dental_Knowledge_Base.pdf`. Do not add facts that are not in
the source document. Known contradictions in the source are recorded in `KNOWN_ISSUES` and rendered
for the model with explicit handling instructions instead of being silently resolved.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class LocationId(StrEnum):
    BETHESDA = "bethesda"
    ROCKVILLE = "rockville"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Location(_Frozen):
    id: LocationId
    name: str
    address: str
    hours: tuple[str, ...]
    notes: tuple[str, ...] = ()


class Service(_Frozen):
    name: str
    price: str


class MembershipPlan(_Frozen):
    monthly_price_usd: int = Field(gt=0)
    includes: str


class Insurance(_Frozen):
    in_network: tuple[str, ...]
    not_accepted: tuple[str, ...]
    out_of_network: str
    membership: MembershipPlan


class KnownIssue(_Frozen):
    topic: str
    conflict: str
    handling: str


class KnowledgeBase(_Frozen):
    practice_name: str
    phone: str
    email: str
    about: str
    locations: tuple[Location, ...]
    insurance: Insurance
    services: tuple[Service, ...]
    pricing_note: str
    new_patient_process: tuple[str, ...]
    emergencies: tuple[str, ...]
    known_issues: tuple[KnownIssue, ...]

    def location(self, location_id: LocationId) -> Location:
        return next(loc for loc in self.locations if loc.id is location_id)


KNOWN_ISSUES = (
    KnownIssue(
        topic="Bethesda Saturday hours",
        conflict=(
            "The About section says Saturdays 8:00 AM to 1:00 PM, but the hours table says "
            "Saturday 9:00 AM to 2:00 PM."
        ),
        handling=(
            "Say the Bethesda office is open Saturday mornings and ask the patient to call "
            "(301) 555-0148 to confirm exact Saturday hours. Never state either time range as fact."
        ),
    ),
)

KB = KnowledgeBase(
    practice_name="Bright Smile Dental",
    phone="(301) 555-0148",
    email="hello@brightsmiledental.example",
    about=(
        "Bright Smile Dental is a family and cosmetic dental practice with two locations in "
        "Montgomery County, Maryland. The Bethesda office is the flagship location and is open on "
        "Saturdays for patients who can't make it in during the week. The Rockville office serves "
        "the north county area on weekdays. New patients are welcome at both locations."
    ),
    locations=(
        Location(
            id=LocationId.BETHESDA,
            name="Bethesda (flagship)",
            address="7315 Wisconsin Ave, Suite 400, Bethesda, MD 20814",
            hours=(
                "Monday to Thursday: 8:00 AM to 5:00 PM",
                "Friday: 8:00 AM to 3:00 PM",
                "Saturday: open in the morning "
                "(exact hours conflict in the source; see known issues)",
            ),
        ),
        Location(
            id=LocationId.ROCKVILLE,
            name="Rockville",
            address="199 E Montgomery Ave, Suite 210, Rockville, MD 20850",
            hours=("Monday to Friday: 8:00 AM to 5:00 PM", "Closed weekends"),
        ),
    ),
    insurance=Insurance(
        in_network=(
            "Delta Dental PPO",
            "Cigna DPPO",
            "MetLife PDP",
            "Aetna Dental PPO",
            "Guardian",
            "United Concordia",
        ),
        not_accepted=("Medicaid", "HMO plans"),
        out_of_network=(
            "For out-of-network plans, the practice provides a superbill patients can submit "
            "for reimbursement."
        ),
        membership=MembershipPlan(
            monthly_price_usd=29,
            includes=("two cleanings, exams, and X-rays per year, plus 15% off other treatment"),
        ),
    ),
    services=(
        Service(
            name="New patient exam + X-rays + cleaning",
            price="$149 new patient special (regularly $310)",
        ),
        Service(name="Routine cleaning (existing patients)", price="$120 to $160"),
        Service(name="Fillings (composite)", price="$210 to $380 per tooth"),
        Service(name="Crowns", price="$1,100 to $1,500"),
        Service(name="Teeth whitening (in-office)", price="$399"),
        Service(name="Invisalign", price="$3,800 to $5,500 (free consultation)"),
        Service(name="Dental implants", price="From $3,900 per tooth (consultation required)"),
        Service(name="Emergency exam", price="$95 (applied to treatment if done the same day)"),
    ),
    pricing_note=(
        "All prices are estimates before insurance. Final cost depends on the treatment plan."
    ),
    new_patient_process=(
        "Book by phone at (301) 555-0148 or request an appointment through the website or chatbot.",
        "The practice collects name, phone, email, reason for visit, and preferred location, then "
        "the front desk calls within one business day to schedule.",
        "Bring a photo ID, your insurance card, and a list of current medications to your first "
        "visit.",
        "Arrive 15 minutes early to complete intake forms, or complete them online in advance.",
    ),
    emergencies=(
        "Dental emergencies during office hours: call (301) 555-0148 and the office will fit you "
        "in the same day when possible.",
        "After hours: existing patients can call the same number for the on-call dentist.",
        "Severe swelling, uncontrolled bleeding, or trauma should go to the nearest emergency "
        "room.",
        "The assistant must not give medical or dental treatment advice. All symptom and "
        "medication questions go to the office.",
    ),
    known_issues=KNOWN_ISSUES,
)


def render_kb(kb: KnowledgeBase = KB) -> str:
    """Render the knowledge base as stable Markdown for the system prompt.

    The output is deterministic so the prompt prefix is byte-identical across requests, which lets
    OpenAI's automatic prompt caching apply.
    """
    lines: list[str] = [
        f"# {kb.practice_name} knowledge base",
        "",
        "## About",
        kb.about,
        "",
        "## Contact",
        f"- Main phone (both locations): {kb.phone}",
        f"- Email: {kb.email}",
        "",
        "## Locations and hours",
    ]
    for loc in kb.locations:
        lines += [f"### {loc.name}", f"- Address: {loc.address}"]
        lines += [f"- {hours}" for hours in loc.hours]
        lines += [f"- {note}" for note in loc.notes]
    ins = kb.insurance
    lines += [
        "",
        "## Insurance",
        f"- In-network: {', '.join(ins.in_network)}",
        f"- Not accepted: {', '.join(ins.not_accepted)}",
        f"- Out-of-network: {ins.out_of_network}",
        f"- In-house membership plan: ${ins.membership.monthly_price_usd}/month, covers "
        f"{ins.membership.includes}",
        "",
        "## Services and typical pricing",
    ]
    lines += [f"- {svc.name}: {svc.price}" for svc in kb.services]
    lines += [f"- Note: {kb.pricing_note}", "", "## New patient process"]
    lines += [f"- {step}" for step in kb.new_patient_process]
    lines += ["", "## Emergencies and medical questions"]
    lines += [f"- {item}" for item in kb.emergencies]
    lines += ["", "## Known issues in this knowledge base"]
    for issue in kb.known_issues:
        lines += [f"- {issue.topic}: {issue.conflict} Handling: {issue.handling}"]
    return "\n".join(lines) + "\n"
