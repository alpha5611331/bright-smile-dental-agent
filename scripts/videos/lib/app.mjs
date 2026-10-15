// How the recording finds its way around this app: the chat widget on the
// landing page and the front-desk dashboard.
//
// Everything is found the way a person or a screen reader finds it, by role and
// accessible name, so a restyle does not break a take. The chat transcript is
// the `role="log"` region, which is `aria-busy` while a reply is on its way.

import { humanClick, humanType, pause, pressKey, scrollWithin } from "./human.mjs";

export const FRONTEND_ORIGIN = process.env.FRONTEND_ORIGIN ?? "http://localhost:3000";

export function oneLine(text) {
  return text.replace(/\s+/g, " ").trim();
}

export async function openScreen(page, route) {
  await page.goto(`${FRONTEND_ORIGIN}${route}`);
  await page.waitForLoadState("networkidle");
  await pause(500);
}

// --- Chat --------------------------------------------------------------------

function chatLog(page) {
  return page.getByRole("dialog").getByRole("log", { name: "Conversation" });
}

function assistantMessages(page) {
  return chatLog(page).locator("[data-slot=message][data-align=start]");
}

/** Wait until the assistant has finished answering. The log is `aria-busy`
 * from the moment a message is sent until the stream ends. */
export async function waitForReply(page, assistantCountBefore) {
  const log = chatLog(page);
  await page.waitForFunction(
    ([before]) => {
      const region = document.querySelector("[role=dialog] [role=log]");
      if (!region || region.getAttribute("aria-busy") !== "false") return false;
      return region.querySelectorAll("[data-slot=message][data-align=start]").length > before;
    },
    [assistantCountBefore],
    { timeout: 90000, polling: 250 },
  );
  await log.waitFor();
  await pause(400);
}

/** The text of the assistant's latest reply. */
export async function lastReply(page) {
  return oneLine(await assistantMessages(page).last().innerText());
}

/** Type a message into the open chat, send it, and wait for the whole answer. */
export async function sendMessage(page, text) {
  const before = await assistantMessages(page).count();
  await humanType(page, page.getByLabel("Your message"), text);
  await pause(250);
  const focused = await page.evaluate(() => document.activeElement?.id ?? document.activeElement?.tagName);
  if (focused !== "chat-message") throw new Error(`Focus is on ${focused}, not the composer, before Enter`);
  await pressKey("ENTER");
  await waitForReply(page, before);
  // Real keystrokes go wherever focus really is, so confirm what was sent.
  const sent = oneLine(await chatLog(page).locator("[data-slot=message][data-align=end]").last().innerText());
  if (sent !== oneLine(text)) throw new Error(`Sent ${JSON.stringify(sent)} instead of ${JSON.stringify(text)}`);
  return lastReply(page);
}

/** Click something that asks the assistant a question (a quick reply, a button
 * on the page) and wait for the answer. */
export async function askBy(page, locator) {
  const open = await page.getByRole("dialog").count();
  const before = open ? await assistantMessages(page).count() : 1;
  await humanClick(page, locator);
  await page.getByRole("dialog").waitFor();
  await waitForReply(page, before);
  return lastReply(page);
}

export async function openChat(page) {
  await humanClick(page, page.getByRole("button", { name: "Ask us a question" }));
  await page.getByRole("dialog").waitFor();
  await pause(600);
}

export async function closeChat(page) {
  await pressKey("ESC");
  await pause(600);
}

/** The notice under the transcript ("Request received"), or null. */
export async function chatNotice(page) {
  const alert = page.getByRole("dialog").getByRole("alert");
  if ((await alert.count()) === 0) return null;
  return oneLine(await alert.first().innerText());
}

/** Wheel the transcript up until the start of the latest reply is in view: the
 * transcript follows the bottom, so a long answer otherwise sits with its
 * first lines above the fold. */
export async function showLatestReply(page) {
  const reply = assistantMessages(page).last();
  const above = await reply.evaluate((el) => {
    const viewport = el.closest("[role=log]").parentElement;
    return el.getBoundingClientRect().top - viewport.getBoundingClientRect().top - 12;
  });
  // Hover the panel, not the transcript content: the content is taller than the
  // panel, so its centre can sit outside the dialog, over the page behind it.
  if (above < 0) await scrollWithin(page, page.getByRole("dialog"), above);
  await pause(400);
}

// --- Dashboard ---------------------------------------------------------------

/** Each row of the leads table, read at desktop width where all six columns show. */
export async function tableRows(page) {
  await page.locator("main tbody tr").first().waitFor();
  return page.locator("main tbody tr").evaluateAll((rows) =>
    rows.map((row) => {
      const cells = [...row.querySelectorAll("td")].map((td) => td.innerText.trim());
      const [name, detail = ""] = cells[1].split("\n").map((part) => part.trim());
      return {
        priority: cells[0],
        name,
        detail,
        office: cells[2],
        received: cells[3],
        callback: cells[4].replace(/\s+/g, " "),
        status: cells[5],
        overdue: /destructive/.test(row.className),
      };
    }),
  );
}

/** The table as a sentence: "P1 Maria Lopez; P2 David Chen; ...". */
export async function orderSentence(page) {
  const rows = await tableRows(page);
  return rows.map((row) => `${row.priority} ${row.name}`).join("; ") || "no leads";
}

/** The value on one stat card, by its label. */
export async function statValue(page, label) {
  const card = page.getByRole("region", { name: "Today at a glance" }).locator("[data-slot=card]").filter({ hasText: label });
  return oneLine(await card.locator("p").first().innerText());
}

/** Choose a value in one of the filter selects (Priority, Office, Sort). */
export async function chooseFilter(page, label, option) {
  await humanClick(page, page.getByRole("combobox", { name: label }));
  await humanClick(page, page.getByRole("option", { name: option, exact: true }));
  await page.waitForLoadState("networkidle");
  await pause(600);
}

/** Pick one of the status tabs ("Open", "New", ..., "All"). */
export async function chooseView(page, label) {
  await humanClick(page, page.getByRole("group", { name: "Show leads" }).getByRole("button", { name: label, exact: true }));
  await page.waitForLoadState("networkidle");
  await pause(600);
}

export function currentQuery(page) {
  return new URL(page.url()).search || "(none)";
}
