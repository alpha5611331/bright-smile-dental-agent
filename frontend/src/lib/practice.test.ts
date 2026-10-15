import { describe, expect, it } from "vitest";

import {
  dollarAmounts,
  emergencyGuidance,
  newPatientSpecial,
  phoneHref,
  practice,
  splitPrice,
} from "./practice";

describe("practice content", () => {
  it("derives the new patient special from the knowledge base", () => {
    expect(newPatientSpecial).toEqual({ price: "$149", regularPrice: "$310" });
  });

  it("extracts dollar amounts from price strings", () => {
    expect(dollarAmounts("$1,100 to $1,500")).toEqual(["$1,100", "$1,500"]);
    expect(dollarAmounts("Free")).toEqual([]);
  });

  it("splits a price into amount and note", () => {
    expect(splitPrice("$3,800 to $5,500 (free consultation)")).toEqual({
      amount: "$3,800 to $5,500",
      note: "free consultation",
    });
    expect(splitPrice("$399")).toEqual({ amount: "$399", note: null });
  });

  it("builds a dialable phone link", () => {
    expect(phoneHref).toBe("tel:+13015550148");
  });

  it("never shows assistant instructions to patients", () => {
    expect(emergencyGuidance.length).toBe(practice.emergencies.length - 1);
    expect(emergencyGuidance.join(" ")).not.toContain("assistant");
  });

  it("never states either conflicting Saturday range on the page", () => {
    const hours = practice.locations.flatMap((location) => location.hours).join(" ");

    expect(hours).not.toContain("8:00 AM to 1:00 PM");
    expect(hours).not.toContain("9:00 AM to 2:00 PM");
  });
});
