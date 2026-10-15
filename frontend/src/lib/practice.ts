import kb from "@/content/kb.json";

/**
 * Practice facts for page copy. Generated from the backend knowledge base
 * (`bright_smile.cli export-kb`), so the site and the assistant never disagree.
 */
export const practice = kb;

export type Location = (typeof kb.locations)[number];
export type Service = (typeof kb.services)[number];

export const phoneHref = `tel:+1${kb.phone.replace(/\D/g, "")}`;
export const emailHref = `mailto:${kb.email}`;

/** Dollar amounts in a KB price string, e.g. "$149 new patient special (regularly $310)". */
export function dollarAmounts(price: string): string[] {
  return price.match(/\$[\d,]+/g) ?? [];
}

/**
 * Split a KB price into the amount and its note, e.g. "$3,800 to $5,500 (free consultation)" becomes
 * { amount: "$3,800 to $5,500", note: "free consultation" }.
 */
export function splitPrice(price: string): { amount: string; note: string | null } {
  const match = /^(.*?)\s*\(([^)]*)\)\s*$/.exec(price);
  return match
    ? { amount: match[1] ?? price, note: match[2] ?? null }
    : { amount: price, note: null };
}

const NEW_PATIENT_SERVICE = "New patient exam + X-rays + cleaning";

function requireService(name: string): Service {
  const service = kb.services.find((s) => s.name === name);
  if (!service) {
    throw new Error(`Service "${name}" is missing from kb.json`);
  }
  return service;
}

const [specialPrice = "", regularPrice = ""] = dollarAmounts(
  requireService(NEW_PATIENT_SERVICE).price,
);

/** The new patient special, split for display. */
export const newPatientSpecial = { price: specialPrice, regularPrice } as const;

/** Emergency guidance for patients (the last KB entry is an instruction for the assistant). */
export const emergencyGuidance = kb.emergencies.filter((line) => !line.includes("assistant"));
