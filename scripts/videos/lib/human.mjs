// Input that looks like a person, driven through the real Windows cursor and
// keyboard (lib/os-input.mjs) rather than Playwright's virtual input.
//
// Page coordinates (what boundingBox returns) are not screen coordinates: the
// browser's own frame offsets the page within the window, even fullscreen.
// calibrate() measures that offset by moving the real cursor to two known
// screen points and asking the page where it saw them, so it is exact by
// construction rather than a guess about border sizes.

let input = null;
let offsetX = 0;
let offsetY = 0;
// Where the cursor is, in page coordinates. Windows is never asked mid-run;
// the next path simply starts here.
let cursorX = 960;
let cursorY = 540;

export function useInput(osInput) {
  input = osInput;
}

export function pause(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function rand(min, max) {
  return min + Math.random() * (max - min);
}

function toScreen(x, y) {
  return [x + offsetX, y + offsetY];
}

export async function calibrate(page) {
  await page.evaluate(() => {
    if (window.__rec_mouseHooked__) return;
    window.__rec_mouseHooked__ = true;
    window.addEventListener("mousemove", (e) => (window.__rec_lastMouse__ = { x: e.clientX, y: e.clientY }), true);
  });

  const samples = [];
  for (const [screenX, screenY] of [
    [600, 420],
    [1100, 640],
  ]) {
    await page.evaluate(() => (window.__rec_lastMouse__ = null));
    // Two nudges: a move to the identical coordinate emits no event.
    await input.moveTo(screenX - 3, screenY - 3);
    await pause(70);
    await input.moveTo(screenX, screenY);
    await pause(160);
    const seen = await page.evaluate(() => window.__rec_lastMouse__);
    if (!seen) throw new Error(`calibrate: the page saw no pointer at screen ${screenX},${screenY}. Is the browser in front?`);
    samples.push({ dx: screenX - seen.x, dy: screenY - seen.y });
  }

  const [a, b] = samples;
  if (Math.abs(a.dx - b.dx) > 2 || Math.abs(a.dy - b.dy) > 2) {
    throw new Error(
      `calibrate: the offset is not constant (${JSON.stringify(a)} vs ${JSON.stringify(b)}). ` +
        "The page is scaled: set Windows display scaling to 100%.",
    );
  }
  offsetX = Math.round((a.dx + b.dx) / 2);
  offsetY = Math.round((a.dy + b.dy) / 2);
  cursorX = 1100 - offsetX;
  cursorY = 640 - offsetY;
  console.log(`  calibrated: page at screen offset ${offsetX},${offsetY}`);
}

/** Travel to a page point along an eased, slightly bowed path, the way a wrist
 * arcs rather than tracking a ruler, with a small overshoot on long moves. */
export async function moveTo(x, y) {
  const startX = cursorX;
  const startY = cursorY;
  const distance = Math.hypot(x - startX, y - startY);
  if (distance < 1) return;

  const steps = Math.max(12, Math.min(48, Math.round(distance / 22)));
  const bow = Math.min(46, distance * 0.11) * (Math.random() < 0.5 ? -1 : 1);
  const perpX = -(y - startY) / distance;
  const perpY = (x - startX) / distance;

  for (let i = 1; i <= steps; i += 1) {
    const t = i / steps;
    const eased = t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2;
    const arc = Math.sin(Math.PI * t) * bow;
    const jitter = i === steps ? 0 : rand(-1.2, 1.2);
    await input.moveTo(...toScreen(startX + (x - startX) * eased + perpX * arc + jitter, startY + (y - startY) * eased + perpY * arc + jitter));
    await pause(rand(7, 15));
  }
  if (distance > 220 && Math.random() < 0.6) {
    await input.moveTo(...toScreen(x + rand(-4, 4), y + rand(-3, 3)));
    await pause(rand(30, 70));
    await input.moveTo(...toScreen(x, y));
  }
  cursorX = x;
  cursorY = y;
}

async function aimAt(locator) {
  await locator.waitFor({ state: "visible" });
  await locator.scrollIntoViewIfNeeded().catch(() => {});
  await pause(rand(120, 240));
  const box = await locator.boundingBox();
  if (!box) throw new Error(`No box for ${locator}`);
  return {
    x: box.x + box.width / 2 + rand(-Math.min(7, box.width / 4), Math.min(7, box.width / 4)),
    y: box.y + box.height / 2 + rand(-Math.min(4, box.height / 4), Math.min(4, box.height / 4)),
  };
}

/** Move the real cursor to the element and click it with the real button. */
export async function humanClick(page, locator) {
  const { x, y } = await aimAt(locator);
  await moveTo(x, y);
  await pause(rand(90, 190));
  await input.click();
  await pause(rand(200, 340));
}

/** Point at something without clicking, to draw the eye to it. */
export async function hover(page, locator) {
  const { x, y } = await aimAt(locator);
  await moveTo(x, y);
  await pause(300);
}

/** Click into a field and type into it with the real keyboard.
 *
 * Checked afterwards: keystrokes go wherever focus really is, so a missed
 * click would put the text somewhere else. That is a failed take, not
 * something to paper over. */
export async function humanType(page, locator, text) {
  await humanClick(page, locator);
  await input.type(text);
  await pause(rand(150, 300));
  const actual = await locator.inputValue().catch(() => null);
  if (actual !== null && actual.trim() !== text.trim()) {
    throw new Error(`Typed text landed as ${JSON.stringify(actual)}, expected ${JSON.stringify(text)}`);
  }
}

/** A real key press: ENTER, ESC, TAB or BACKSPACE. */
export async function pressKey(name) {
  await input.key(name);
  await pause(rand(150, 260));
}

/** Scroll with the real wheel, over whatever is under the cursor. */
export async function scrollBy(page, dy) {
  const notches = Math.max(1, Math.round(Math.abs(dy) / 100));
  for (let i = 0; i < notches; i += 1) {
    await input.wheel(Math.sign(dy) * 100);
    await pause(rand(40, 80));
  }
  await pause(500);
}

/** Put the cursor over a region (the chat transcript, the lead sheet) and
 * scroll it with the real wheel. */
export async function scrollWithin(page, locator, dy) {
  await hover(page, locator);
  await scrollBy(page, dy);
}

/** Wheel the page until `locator` is comfortably inside the viewport. */
export async function wheelUntilVisible(page, locator, { maxNotches = 40 } = {}) {
  await locator.waitFor();
  const height = await page.evaluate(() => window.innerHeight);
  for (let i = 0; i < maxNotches; i += 1) {
    const box = await locator.boundingBox();
    if (box && box.y > 80 && box.y + box.height < height * 0.75) break;
    await input.wheel(box && box.y < 80 ? -100 : 100);
    await pause(rand(40, 80));
  }
  await pause(500);
}
