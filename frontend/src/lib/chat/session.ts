import type { ChatStreamEvent } from "./sse";

export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
}

/** Something the visitor should know that is not a chat message. */
export type ChatNotice =
  | { kind: "lead_captured" }
  | { kind: "rate_limited"; retryAfterSeconds: number }
  | { kind: "limit_reached"; message: string }
  | { kind: "error"; message: string };

export type ChatStatus = "idle" | "waiting" | "streaming";

export interface ChatState {
  messages: ChatMessage[];
  status: ChatStatus;
  notice: ChatNotice | null;
  /** Text to restore into the composer when a send fails, so nothing typed is lost. */
  retryText: string | null;
}

export const initialChatState: ChatState = {
  messages: [],
  status: "idle",
  notice: null,
  retryText: null,
};

export type ChatAction =
  | { type: "send"; id: string; text: string }
  | { type: "stream_event"; event: ChatStreamEvent; assistantId: string }
  | { type: "request_failed"; notice: ChatNotice; text: string }
  | { type: "finished" }
  | { type: "dismiss_notice" };

function appendToken(messages: ChatMessage[], assistantId: string, text: string): ChatMessage[] {
  const last = messages.at(-1);
  if (last?.id === assistantId) {
    return [...messages.slice(0, -1), { ...last, text: last.text + text }];
  }
  return [...messages, { id: assistantId, role: "assistant", text }];
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "send":
      return {
        messages: [...state.messages, { id: action.id, role: "user", text: action.text }],
        status: "waiting",
        notice: state.notice?.kind === "lead_captured" ? state.notice : null,
        retryText: null,
      };
    case "stream_event": {
      const { event } = action;
      switch (event.type) {
        case "token":
          return {
            ...state,
            status: "streaming",
            messages: appendToken(state.messages, action.assistantId, event.text),
          };
        case "lead_captured":
          return { ...state, notice: { kind: "lead_captured" } };
        case "error":
          return { ...state, status: "idle", notice: { kind: "error", message: event.message } };
        case "done":
          return { ...state, status: "idle" };
        case "conversation":
        case "flag":
          return state;
      }
      return state;
    }
    case "request_failed":
      return {
        // Drop the optimistic user message: it never reached the assistant.
        messages: state.messages.slice(0, -1),
        status: "idle",
        notice: action.notice,
        retryText: action.text,
      };
    case "finished":
      return state.status === "idle" ? state : { ...state, status: "idle" };
    case "dismiss_notice":
      return { ...state, notice: null };
  }
}
