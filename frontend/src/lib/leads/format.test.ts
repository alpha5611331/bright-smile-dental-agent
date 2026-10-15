import { describe, expect, it } from "vitest";

import { formatAgo, formatPhone, formatPracticeTime, slaStatus } from "./format";

const NOW = new Date("2026-10-14T18:00:00Z"); // Wed 2:00 PM in New York

describe("slaStatus", () => {
  it("counts down for new leads", () => {
    expect(slaStatus({ status: "new", sla_due_at: "2026-10-15T21:00:00Z" }, NOW)).toEqual({
      tone: "on_track",
      label: "Due in 27 h",
    });
  });

  it("flags leads due within four hours", () => {
    expect(slaStatus({ status: "new", sla_due_at: "2026-10-14T20:30:00Z" }, NOW)).toEqual({
      tone: "due_soon",
      label: "Due in 3 h",
    });
  });

  it("reports how overdue a lead is", () => {
    expect(slaStatus({ status: "new", sla_due_at: "2026-10-14T17:15:00Z" }, NOW)).toEqual({
      tone: "overdue",
      label: "Overdue by 45 min",
    });
  });

  it("closes the SLA once the lead left new", () => {
    expect(slaStatus({ status: "contacted", sla_due_at: "2026-10-10T21:00:00Z" }, NOW).tone).toBe(
      "closed",
    );
  });
});

describe("formatting", () => {
  it("shows times in practice time, not the browser's zone", () => {
    expect(formatPracticeTime("2026-10-14T19:05:00Z")).toBe("Wed, Oct 14, 3:05 PM");
  });

  it("describes how long ago something happened", () => {
    expect(formatAgo("2026-10-14T17:55:00Z", NOW)).toBe("5 minutes ago");
    expect(formatAgo("2026-10-13T18:00:00Z", NOW)).toBe("yesterday");
    expect(formatAgo("2026-10-14T17:59:50Z", NOW)).toBe("just now");
  });

  it("formats US phone numbers", () => {
    expect(formatPhone("+13016521234")).toBe("(301) 652-1234");
    expect(formatPhone("+442079460958")).toBe("+442079460958");
  });
});
