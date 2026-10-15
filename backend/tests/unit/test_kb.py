"""The knowledge base must stay faithful to context/Bright_Smile_Dental_Knowledge_Base.pdf."""

from bright_smile.agent.kb import KB, LocationId, render_kb

EM_DASH = chr(0x2014)


def test_contact_details() -> None:
    assert KB.phone == "(301) 555-0148"
    assert KB.email == "hello@brightsmiledental.example"


def test_locations() -> None:
    bethesda = KB.location(LocationId.BETHESDA)
    rockville = KB.location(LocationId.ROCKVILLE)

    assert bethesda.address == "7315 Wisconsin Ave, Suite 400, Bethesda, MD 20814"
    assert rockville.address == "199 E Montgomery Ave, Suite 210, Rockville, MD 20850"
    assert "Closed weekends" in rockville.hours


def test_insurance() -> None:
    assert KB.insurance.in_network == (
        "Delta Dental PPO",
        "Cigna DPPO",
        "MetLife PDP",
        "Aetna Dental PPO",
        "Guardian",
        "United Concordia",
    )
    assert KB.insurance.not_accepted == ("Medicaid", "HMO plans")
    assert KB.insurance.membership.monthly_price_usd == 29


def test_service_prices() -> None:
    prices = {svc.name: svc.price for svc in KB.services}

    assert prices["Crowns"] == "$1,100 to $1,500"
    assert prices["New patient exam + X-rays + cleaning"].startswith("$149")
    assert "free consultation" in prices["Invisalign"]
    assert "free" not in prices["Dental implants"]
    assert "consultation required" in prices["Dental implants"]


def test_saturday_hours_are_never_stated_as_fact_outside_known_issues() -> None:
    bethesda_hours = " ".join(KB.location(LocationId.BETHESDA).hours)

    assert "8:00 AM to 1:00 PM" not in bethesda_hours
    assert "9:00 AM to 2:00 PM" not in bethesda_hours
    issue = KB.known_issues[0]
    assert "8:00 AM to 1:00 PM" in issue.conflict
    assert "9:00 AM to 2:00 PM" in issue.conflict
    assert "Never state either time range" in issue.handling


def test_render_is_deterministic_and_clean() -> None:
    rendered = render_kb()

    assert rendered == render_kb()
    assert EM_DASH not in rendered
    for section in ("## Insurance", "## Services and typical pricing", "## Known issues"):
        assert section in rendered
