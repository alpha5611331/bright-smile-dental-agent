// Video 4: The front-desk dashboard.
// SPEC US-5, US-6, sections 6.3, 6.4, 8.3.
//
// Staff sign in and work the queue: the stat cards, the order the table puts
// callbacks in, an overdue callback, the request Video 3 captured in the chat
// (with its safety flag and transcript), a status change and a note, then the
// filters and the link they live in.
//
// The rest of the week was seeded off camera by seed.py, through the backend's
// own rules. Every figure a caption quotes is read off the screen.

import {
  chooseFilter,
  chooseView,
  currentQuery,
  oneLine,
  openScreen,
  orderSentence,
  statValue,
  tableRows,
} from "../lib/app.mjs";
import { expect } from "../lib/beats.mjs";
import { hover, humanClick, humanType, pause, pressKey, scrollWithin } from "../lib/human.mjs";
import { CHAT_PATIENT, FORM_PATIENT } from "./video3.mjs";

async function toastText(page) {
  const toast = page.locator("[data-sonner-toast]").last();
  await toast.waitFor();
  return oneLine(await toast.innerText());
}

function row(page, name) {
  return page.locator("main tbody tr").filter({ hasText: name }).first();
}

export default [
  {
    title: true,
    caption: "Video 4: The front-desk dashboard",
    action: async (page) => {
      await openScreen(page, "/dashboard");
    },
    holdMs: 2600,
  },
  {
    read: async (page, state) => {
      state.v4LoginUrl = new URL(page.url()).pathname + new URL(page.url()).search;
    },
    caption: (state) =>
      `The dashboard is staff only. Opening it signed out lands on ${decodeURIComponent(state.v4LoginUrl)}, and signing in returns to where you were going.`,
    action: async (page, state) => {
      await pause(2500);
      await humanType(page, page.getByLabel("Staff password"), state.staffPassword);
      await humanClick(page, page.getByRole("button", { name: "Log in" }));
      await page.waitForURL(/\/dashboard(\?|$)/);
      await page.locator("main tbody tr").first().waitFor();
      await page.waitForLoadState("networkidle");
    },
    holdMs: 1200,
  },
  {
    read: async (page, state) => {
      state.v4NewToday = await statValue(page, "New today");
      state.v4Overdue = await statValue(page, "Overdue callbacks");
      state.v4HighValue = await statValue(page, "High-value consults");
      state.v4AfterHours = await statValue(page, "After-hours share");
    },
    caption: (state) =>
      `Today at a glance: ${state.v4NewToday} new today, ${state.v4Overdue} overdue, ${state.v4HighValue} open high-value consults, and ${state.v4AfterHours} of requests arrived while both offices were closed. Those are leads a phone-only front desk would have missed.`,
    action: async (page) => {
      await hover(page, page.getByRole("region", { name: "Today at a glance" }));
    },
    holdMs: 9500,
  },
  {
    read: async (page, state) => {
      state.v4Order = await orderSentence(page);
    },
    caption: (state) =>
      `The open queue, in the order to call: ${state.v4Order}. Priority is computed in code: emergencies first, then high-value consults, then new patients.`,
    holdMs: 10000,
  },
  {
    read: async (page, state) => {
      const overdue = (await tableRows(page)).find((r) => r.overdue);
      expect(overdue, "No overdue row in the open queue; reseed before the take.");
      state.v4OverdueName = overdue.name;
      state.v4OverdueText = overdue.callback;
    },
    caption: (state) =>
      `Every request carries a one-business-day callback timer. ${state.v4OverdueName}'s ran out ("${state.v4OverdueText}"), so the row is tinted red.`,
    action: async (page, state) => {
      await hover(page, row(page, state.v4OverdueName).locator("td").nth(4));
    },
    holdMs: 8000,
  },
  {
    caption: `${CHAT_PATIENT.name}, captured by the chat in Video 3. Opening the row shows everything needed to make the call.`,
    action: async (page) => {
      await humanClick(page, row(page, CHAT_PATIENT.name).getByRole("button", { name: new RegExp(CHAT_PATIENT.name) }));
      await page.getByRole("dialog").getByRole("heading", { name: CHAT_PATIENT.name }).waitFor();
      await pause(800);
    },
    holdMs: 1200,
  },
  {
    read: async (page, state) => {
      const sheet = page.getByRole("dialog");
      state.v4SheetSummary = oneLine(await sheet.locator("[data-slot=sheet-description]").innerText());
      const alert = sheet.getByRole("alert");
      state.v4Flags = (await alert.count()) ? oneLine(await alert.innerText()) : "no flags";
    },
    caption: (state) =>
      `${state.v4SheetSummary} One tap to call or email, and a warning to read first: "${state.v4Flags}". That is the bleeding-gums question from the chat.`,
    action: async (page) => {
      await hover(page, page.getByRole("dialog").getByRole("alert"));
    },
    holdMs: 9500,
  },
  {
    caption: "Below the details, the whole chat transcript, so nobody has to ask the patient to repeat themselves.",
    action: async (page) => {
      const sheet = page.getByRole("dialog");
      await scrollWithin(page, sheet, 700);
      await pause(2500);
      await scrollWithin(page, sheet, 600);
      await pause(2000);
      await scrollWithin(page, sheet, -2500);
    },
    holdMs: 1500,
  },
  {
    caption: "The front desk calls Jordan and marks the request Contacted.",
    action: async (page) => {
      await humanClick(page, page.getByLabel("Status"));
      await humanClick(page, page.getByRole("option", { name: "Contacted", exact: true }));
    },
    holdMs: 400,
  },
  {
    read: async (page, state) => {
      state.v4StatusToast = await toastText(page);
    },
    caption: (state) => `The change shows at once and is confirmed: "${state.v4StatusToast}" If the save failed, it would roll back and say so.`,
    action: async (page) => {
      await humanType(page, page.getByLabel("Notes"), "Booked the Invisalign consult for Thursday at 10 AM. Mentioned the gums question to the hygienist.");
      await humanClick(page, page.getByRole("button", { name: "Save notes" }));
    },
    holdMs: 600,
  },
  {
    read: async (page, state) => {
      await pause(600);
      state.v4NotesToast = await toastText(page);
    },
    caption: (state) => `Notes are saved the same way: "${state.v4NotesToast}"`,
    action: async (page) => {
      await pause(2500);
      await pressKey("ESC");
      await pause(800);
    },
    holdMs: 600,
  },
  {
    read: async (page, state) => {
      const jordan = (await tableRows(page)).find((r) => r.name === CHAT_PATIENT.name);
      state.v4JordanNow = jordan ? `${jordan.status}, ${jordan.callback}` : "not in the open view";
      const sam = (await tableRows(page)).find((r) => r.name === FORM_PATIENT.name);
      state.v4Sam = sam ? `${sam.priority}, ${sam.detail}` : "missing";
    },
    check: (state) => {
      expect(state.v4Sam !== "missing", `${FORM_PATIENT.name}'s form request is not in the queue`);
      expect(state.v4JordanNow.startsWith("Contacted"), `Status change not shown: ${state.v4JordanNow}`);
    },
    caption: (state) =>
      `Back in the queue, Jordan now reads "${state.v4JordanNow}". ${FORM_PATIENT.name}, from the form, is here too (${state.v4Sam}).`,
    holdMs: 8000,
  },
  {
    caption: "Filters: high-value consults at Bethesda only.",
    action: async (page) => {
      await chooseFilter(page, "Priority", "P2 High value");
      await chooseFilter(page, "Office", "Bethesda");
    },
    holdMs: 600,
  },
  {
    read: async (page, state) => {
      state.v4Filtered = await orderSentence(page);
      state.v4Query = currentQuery(page);
    },
    caption: (state) =>
      `Showing ${state.v4Filtered}. The filters live in the address (${state.v4Query}), so a view can be bookmarked or sent to a colleague, and it survives a reload.`,
    action: async (page) => {
      await pause(4500);
      await page.reload();
      await page.waitForLoadState("networkidle");
      await pause(1200);
    },
    holdMs: 1200,
  },
  {
    read: async (page, state) => {
      state.v4AfterReload = await orderSentence(page);
    },
    caption: (state) => `After the reload: ${state.v4AfterReload}. Same view.`,
    holdMs: 5000,
  },
  {
    caption: 'The "All" view brings back finished requests too: scheduled, and not interested.',
    action: async (page) => {
      await chooseFilter(page, "Priority", "All priorities");
      await chooseFilter(page, "Office", "All offices");
      await chooseView(page, "All");
    },
    holdMs: 600,
  },
  {
    read: async (page, state) => {
      const rows = await tableRows(page);
      state.v4AllCount = String(rows.length);
      state.v4Closed = rows.filter((r) => r.status === "Scheduled" || r.status === "Not interested").map((r) => `${r.name} (${r.status})`).join(", ");
    },
    caption: (state) =>
      `${state.v4AllCount} requests in all, including ${state.v4Closed}. The list refreshes every minute and whenever the window regains focus, so new requests appear without a reload.`,
    holdMs: 9000,
  },
];
