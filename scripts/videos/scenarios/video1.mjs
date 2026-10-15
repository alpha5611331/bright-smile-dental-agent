// Video 1: Answers from the knowledge base.
// SPEC US-1, sections 4.1, 4.2, 4.5, 4.6.
//
// A visitor on the landing page. One question from the page's own buttons,
// three typed into the chat: a price, two insurance questions, and the Saturday
// hours the KB contradicts itself on. Every reply is read off the screen and
// checked before its caption is drawn.

import { askBy, openScreen, sendMessage, showLatestReply } from "../lib/app.mjs";
import { expect } from "../lib/beats.mjs";
import { hover, pause, scrollBy } from "../lib/human.mjs";
import { mentionsPhone, noSaturdayTimes, opening } from "./checks.mjs";

export default [
  {
    title: true,
    caption: "Bright Smile Dental AI Front Desk\nVideo 1: Answers from the knowledge base",
    action: async (page) => {
      await openScreen(page, "/");
    },
    holdMs: 3200,
  },
  {
    caption:
      "The practice's website. Every price, hour and insurer on this page is generated from the same knowledge base the assistant answers from, so the two can never disagree.",
    action: async (page) => {
      await hover(page, page.getByRole("heading", { name: "New patient visit" }));
      await pause(1500);
      await scrollBy(page, 900);
      await pause(1800);
      await scrollBy(page, -900);
    },
    holdMs: 1800,
  },
  {
    caption: 'A visitor clicks one of the common questions on the page: "How much is Invisalign?"',
    action: async (page, state) => {
      state.v1Invisalign = await askBy(page, page.getByRole("button", { name: "How much is Invisalign?" }));
      await showLatestReply(page);
    },
    holdMs: 1200,
  },
  {
    check: (state) => {
      expect(/3,800/.test(state.v1Invisalign) && /5,500/.test(state.v1Invisalign), `No KB price range: ${state.v1Invisalign}`);
      expect(/free/i.test(state.v1Invisalign), `Free consultation not mentioned: ${state.v1Invisalign}`);
      expect(/before insurance|estimate/i.test(state.v1Invisalign), `Not framed as an estimate: ${state.v1Invisalign}`);
    },
    caption:
      "The chat opens and streams the answer: the KB's $3,800 to $5,500 range as an estimate before insurance, plus the free Invisalign consultation, mentioned once.",
    holdMs: 9000,
  },
  {
    caption: "Insurance is the question the front desk hears most. The visitor types it.",
    action: async (page, state) => {
      state.v1Cigna = await sendMessage(page, "I have Cigna. Are you in network?");
      await showLatestReply(page);
    },
    holdMs: 1200,
  },
  {
    check: (state) => {
      expect(/cigna/i.test(state.v1Cigna) && /in[- ]network/i.test(state.v1Cigna), `Cigna not confirmed in network: ${state.v1Cigna}`);
    },
    caption: (state) => `Cigna DPPO is on the KB's in-network list. The reply opens: "${opening(state.v1Cigna)}"`,
    holdMs: 8000,
  },
  {
    caption: "Medicaid is one the practice does not take. The assistant says so politely and points to the membership plan.",
    action: async (page, state) => {
      state.v1Medicaid = await sendMessage(page, "What about Medicaid?");
      await showLatestReply(page);
    },
    holdMs: 1200,
  },
  {
    check: (state) => {
      expect(/membership/i.test(state.v1Medicaid), `Membership plan not offered: ${state.v1Medicaid}`);
    },
    caption: "Declined, with the $29 a month membership plan as the alternative. That is a revenue path instead of a dead end.",
    holdMs: 8000,
  },
  {
    caption:
      "The KB contradicts itself on Saturday hours: one section says 8 AM to 1 PM, the hours table says 9 AM to 2 PM. Watch how the assistant handles it.",
    action: async (page, state) => {
      state.v1Saturday = await sendMessage(page, "Are you open on Saturdays?");
      await showLatestReply(page);
    },
    holdMs: 1200,
  },
  {
    check: (state) => {
      noSaturdayTimes(state.v1Saturday);
      expect(/bethesda/i.test(state.v1Saturday), `Bethesda not named: ${state.v1Saturday}`);
      mentionsPhone(state.v1Saturday, "Saturday");
    },
    caption:
      "It says Bethesda is open Saturday mornings and asks the patient to call to confirm the exact time. It never states either range as fact. The conflict is listed in the report for the practice to fix.",
    holdMs: 10000,
  },
];
