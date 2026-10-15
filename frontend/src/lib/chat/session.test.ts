import { describe, expect, it } from "vitest";

import { chatReducer, initialChatState, type ChatState } from "./session";

function sent(text = "Do you take Cigna?"): ChatState {
  return chatReducer(initialChatState, { type: "send", id: "u1", text });
}

describe("chatReducer", () => {
  it("adds the user message and waits for the reply", () => {
    const state = sent();

    expect(state.messages).toEqual([{ id: "u1", role: "user", text: "Do you take Cigna?" }]);
    expect(state.status).toBe("waiting");
  });

  it("streams tokens into a single assistant message", () => {
    let state = sent();
    for (const text of ["Yes, ", "Cigna ", "DPPO."]) {
      state = chatReducer(state, {
        type: "stream_event",
        assistantId: "a1",
        event: { type: "token", text },
      });
    }

    expect(state.status).toBe("streaming");
    expect(state.messages.at(-1)).toEqual({
      id: "a1",
      role: "assistant",
      text: "Yes, Cigna DPPO.",
    });
  });

  it("finishes on done and keeps the lead confirmation across the next send", () => {
    let state = chatReducer(sent(), {
      type: "stream_event",
      assistantId: "a1",
      event: { type: "lead_captured", lead_id: "l1", priority: "P2" },
    });
    state = chatReducer(state, {
      type: "stream_event",
      assistantId: "a1",
      event: { type: "done" },
    });

    expect(state.status).toBe("idle");
    expect(chatReducer(state, { type: "send", id: "u2", text: "Thanks" }).notice).toEqual({
      kind: "lead_captured",
    });
  });

  it("shows stream errors as a notice", () => {
    const state = chatReducer(sent(), {
      type: "stream_event",
      assistantId: "a1",
      event: { type: "error", code: "upstream_unavailable", message: "Please call us." },
    });

    expect(state.status).toBe("idle");
    expect(state.notice).toEqual({ kind: "error", message: "Please call us." });
  });

  it("rolls back a failed request and keeps the text for a retry", () => {
    const state = chatReducer(sent("Hello"), {
      type: "request_failed",
      notice: { kind: "rate_limited", retryAfterSeconds: 30 },
      text: "Hello",
    });

    expect(state.messages).toEqual([]);
    expect(state.retryText).toBe("Hello");
    expect(state.notice).toEqual({ kind: "rate_limited", retryAfterSeconds: 30 });
  });
});
