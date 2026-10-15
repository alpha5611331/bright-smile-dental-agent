// Video 3: A request captured in the chat, and the form for people who prefer one.
// SPEC US-2, sections 3 (US-4), 5.1, 8.2.
//
// A new patient books the free Invisalign consultation from the offer on the
// page. On the way they ask about bleeding gums, which flags the conversation
// for staff (Video 4 shows the flag on the dashboard). Then a second visitor
// uses the form fallback, including what happens when it is sent empty.
//
// The assistant is a real model, so how many turns it takes to confirm the
// details varies. The take answers its questions until the "Request received"
// notice appears, and fails if it never does.

import { askBy, chatNotice, openScreen, sendMessage, showLatestReply } from "../lib/app.mjs";
import { expect } from "../lib/beats.mjs";
import { humanClick, humanType, pause, wheelUntilVisible } from "../lib/human.mjs";
import { mentionsPhone, noDosage, opening } from "./checks.mjs";

export const CHAT_PATIENT = {
  name: "Jordan Avery",
  details:
    "I'm Jordan Avery and I'm a new patient, booking the free Invisalign consultation. My phone is 240-555-0199 and my email is jordan.avery@example.com. The Bethesda office is best, and yes, you can call or email me about this.",
};

export const FORM_PATIENT = {
  name: "Sam Rivera",
  phone: "(301) 555-0177",
  email: "sam.rivera@example.com",
  reason: "New patient exam and cleaning.",
};

const MAX_CONFIRMATIONS = 3;

export default [
  {
    title: true,
    caption: "Video 3: A request captured in the chat",
    action: async (page) => {
      await openScreen(page, "/");
    },
    holdMs: 2600,
  },
  {
    caption: 'A visitor scrolls to the offers and clicks "Book a free consultation" under Invisalign.',
    action: async (page, state) => {
      const button = page.getByRole("button", { name: "Book a free consultation" });
      await wheelUntilVisible(page, button);
      await pause(800);
      state.v3First = await askBy(page, button);
      await showLatestReply(page);
    },
    holdMs: 1200,
  },
  {
    caption: (state) =>
      `The assistant starts collecting what the front desk needs, a few details at a time: "${opening(state.v3First, 220)}"`,
    holdMs: 8000,
  },
  {
    caption: "Before answering, the visitor asks something medical.",
    action: async (page, state) => {
      state.v3Gums = await sendMessage(page, "Before that, my gums bleed a little when I brush. Should I be worried?");
      await showLatestReply(page);
    },
    holdMs: 1200,
  },
  {
    check: (state) => {
      noDosage(state.v3Gums);
      mentionsPhone(state.v3Gums, "Bleeding gums");
    },
    caption: "No diagnosis: it suggests asking the dentist or calling the office, and the conversation is quietly flagged for the front desk.",
    holdMs: 7000,
  },
  {
    caption: "Now the visitor gives their details in one message, the way people actually type.",
    action: async (page, state) => {
      state.v3Reply = await sendMessage(page, CHAT_PATIENT.details);
      // Answer confirmation questions until the request is captured.
      for (let turn = 0; turn < MAX_CONFIRMATIONS && !(await chatNotice(page))?.includes("Request received"); turn += 1) {
        await pause(2500);
        state.v3Reply = await sendMessage(page, "Yes, that's all correct. Please send it.");
      }
      state.v3Notice = (await chatNotice(page)) ?? "none";
      await showLatestReply(page);
    },
    holdMs: 1200,
  },
  {
    check: (state) => {
      expect(state.v3Notice.includes("Request received"), `No lead captured. Notice: ${state.v3Notice}. Reply: ${state.v3Reply}`);
      expect(/business day/i.test(state.v3Reply), `No callback promise: ${state.v3Reply}`);
      expect(/photo ID|insurance card|medication/i.test(state.v3Reply), `Nothing on what to bring: ${state.v3Reply}`);
    },
    caption:
      'The details are validated (US phone, real email, consent) and saved as a lead. "Request received" appears, and the reply says the front desk will call within one business day and what to bring. It never promises an appointment time.',
    holdMs: 11000,
  },
  {
    caption: 'Not everyone wants to chat. "Prefer a form?" opens the same request as a form.',
    action: async (page) => {
      await humanClick(page, page.getByRole("button", { name: "Prefer a form?" }));
      await pause(800);
      await humanClick(page, page.getByRole("button", { name: "Send request" }));
    },
    holdMs: 1200,
  },
  {
    read: async (page, state) => {
      state.v3FormErrors = String(await page.getByRole("dialog").locator("[data-slot=field-error]").count());
    },
    caption: (state) =>
      `Sent empty, it explains what is missing next to each field (${state.v3FormErrors} messages), with the same rules the server applies.`,
    holdMs: 5500,
  },
  {
    caption: "Filled in properly, by a second visitor who prefers Rockville.",
    action: async (page) => {
      const dialog = page.getByRole("dialog");
      await humanType(page, dialog.getByRole("textbox", { name: "Full name" }), FORM_PATIENT.name);
      await humanType(page, dialog.getByRole("textbox", { name: "Phone" }), FORM_PATIENT.phone);
      await humanType(page, dialog.getByRole("textbox", { name: "Email" }), FORM_PATIENT.email);
      await humanType(page, dialog.getByRole("textbox", { name: "What is the visit for?" }), FORM_PATIENT.reason);
      await humanClick(page, dialog.getByRole("combobox", { name: "Preferred office" }));
      await humanClick(page, page.getByRole("option", { name: "Rockville", exact: true }));
      await humanClick(page, dialog.getByRole("checkbox", { name: /may call or email me/ }));
      await pause(600);
      await humanClick(page, dialog.getByRole("button", { name: "Send request" }));
    },
    holdMs: 600,
  },
  {
    read: async (page, state) => {
      const toast = page.locator("[data-sonner-toast]").first();
      await toast.waitFor();
      state.v3Toast = (await toast.innerText()).replace(/\s+/g, " ").trim();
    },
    // The form is rate limited to 5 an hour per IP, in the backend's memory:
    // after a few dry runs, restart the backend before a take.
    check: (state) => {
      expect(state.v3Toast.startsWith("Request sent"), `The form was not accepted: ${state.v3Toast}`);
    },
    caption: (state) => `"${state.v3Toast}" Both requests are now waiting on the front desk's dashboard.`,
    holdMs: 6500,
  },
];
