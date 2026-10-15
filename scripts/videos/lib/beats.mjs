// A video is a list of beats. Each beat draws a caption, runs an action, and
// holds long enough for the caption to be read.
//
// A beat that quotes something off the screen says so with `read`, which runs
// at the end of the previous beat's action, before this beat's caption is drawn.
// Otherwise the caption would be computed before the figure it quotes existed.
//
// A beat can also `check` what it read. The assistant is a real model, so its
// wording changes from take to take; a check is how a take that broke a rule
// (stated a Saturday time, called the implant consult free) stops the run
// instead of ending up in a video.

import { setCaption } from "./overlay.mjs";
import { pause } from "./human.mjs";

export class TakeFailed extends Error {}

/** Throw unless `condition` holds. Used by beats' `check`. */
export function expect(condition, message) {
  if (!condition) throw new TakeFailed(message);
}

function normalise(beats) {
  const out = [];
  for (const beat of beats) {
    const { read, check, ...rest } = beat;
    if (read || check) {
      const previous = out[out.length - 1];
      if (!previous) throw new Error("A beat's read or check needs a beat before it to run in");
      const before = previous.action;
      previous.action = async (page, state) => {
        if (before) await before(page, state);
        if (read) await read(page, state);
        if (check) await check(state);
      };
    }
    if (typeof rest.caption === "function") {
      const compose = rest.caption;
      rest.caption = (state) => {
        const text = compose(state);
        if (/\b(undefined|null|NaN)\b/.test(text)) throw new TakeFailed(`Caption quotes a figure not read yet: ${text}`);
        return text;
      };
    }
    out.push(rest);
  }
  return out;
}

/** Play one video's beats against `page`. `state` is shared across the run. */
export async function playBeats(page, beats, state) {
  for (const beat of normalise(beats)) {
    const caption = typeof beat.caption === "function" ? beat.caption(state) : beat.caption;
    await setCaption(page, caption ?? "", { title: Boolean(beat.title) });
    if (beat.action) await beat.action(page, state);
    await pause(beat.holdMs ?? 1600);
  }
}
