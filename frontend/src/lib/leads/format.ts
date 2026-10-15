import type { components } from "@/lib/api/schema";

type Schemas = components["schemas"];
export type Lead = Schemas["LeadOut"];
export type LeadDetail = Schemas["LeadDetail"];
export type LeadPage = Schemas["LeadPage"];
export type LeadStatus = Schemas["LeadStatus"];
export type Priority = Schemas["Priority"];
export type Interest = Schemas["Interest"];
export type PreferredLocation = Schemas["PreferredLocation"];
export type LeadSort = Schemas["LeadSort"];

export const PRACTICE_TIME_ZONE = "America/New_York";

export const STATUS_LABELS: Record<LeadStatus, string> = {
  new: "New",
  contacted: "Contacted",
  scheduled: "Scheduled",
  not_interested: "Not interested",
};

export const PRIORITY_LABELS: Record<Priority, string> = {
  P1: "P1 Urgent",
  P2: "P2 High value",
  P3: "P3 New patient",
  P4: "P4 Other",
};

export const INTEREST_LABELS: Record<Interest, string> = {
  new_patient_exam: "New patient exam",
  cleaning: "Cleaning",
  filling: "Filling",
  crown: "Crown",
  whitening: "Whitening",
  invisalign: "Invisalign",
  implant: "Implant",
  emergency: "Emergency",
  insurance_question: "Insurance question",
  other: "Other",
};

export const LOCATION_LABELS: Record<PreferredLocation, string> = {
  bethesda: "Bethesda",
  rockville: "Rockville",
  no_preference: "No preference",
};

export const SORT_LABELS: Record<LeadSort, string> = {
  priority: "Priority, oldest first",
  newest: "Newest first",
  oldest: "Oldest first",
};

/** Statuses that still need front-desk work. */
export const OPEN_STATUSES: readonly LeadStatus[] = ["new", "contacted"];

export type SlaTone = "overdue" | "due_soon" | "on_track" | "closed";

const HOUR = 60 * 60 * 1000;

function humanDuration(ms: number): string {
  const minutes = Math.max(1, Math.round(ms / 60_000));
  if (minutes < 60) {
    return `${minutes} min`;
  }
  const hours = Math.round(minutes / 60);
  if (hours < 48) {
    return `${hours} h`;
  }
  return `${Math.round(hours / 24)} days`;
}

/** Callback deadline for a lead, relative to `now` (SPEC section 6.4). */
export function slaStatus(
  lead: Pick<Lead, "status" | "sla_due_at">,
  now: Date,
): { tone: SlaTone; label: string } {
  if (lead.status !== "new") {
    return { tone: "closed", label: "Called back" };
  }
  const remaining = new Date(lead.sla_due_at).getTime() - now.getTime();
  if (remaining < 0) {
    return { tone: "overdue", label: `Overdue by ${humanDuration(-remaining)}` };
  }
  return {
    tone: remaining <= 4 * HOUR ? "due_soon" : "on_track",
    label: `Due in ${humanDuration(remaining)}`,
  };
}

const dateTimeFormat = new Intl.DateTimeFormat("en-US", {
  timeZone: PRACTICE_TIME_ZONE,
  weekday: "short",
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

/** A timestamp in practice time, e.g. "Wed, Oct 14, 3:05 PM". */
export function formatPracticeTime(iso: string): string {
  return dateTimeFormat.format(new Date(iso));
}

const relativeFormat = new Intl.RelativeTimeFormat("en-US", { numeric: "auto" });

/** "5 minutes ago", "yesterday", "3 days ago". */
export function formatAgo(iso: string, now: Date): string {
  const seconds = Math.round((new Date(iso).getTime() - now.getTime()) / 1000);
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ["day", 86_400],
    ["hour", 3_600],
    ["minute", 60],
  ];
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) {
      return relativeFormat.format(Math.round(seconds / size), unit);
    }
  }
  return "just now";
}

/** E.164 US number to "(301) 652-1234". */
export function formatPhone(e164: string): string {
  const digits = e164.replace(/\D/g, "").replace(/^1/, "");
  return digits.length === 10
    ? `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`
    : e164;
}
