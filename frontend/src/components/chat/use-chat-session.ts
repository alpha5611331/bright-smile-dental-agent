"use client";

import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import { api } from "@/lib/api/client";
import { chatReducer, initialChatState, type ChatNotice } from "@/lib/chat/session";
import { readChatEvents } from "@/lib/chat/sse";
import { practice } from "@/lib/practice";

const CONVERSATION_KEY = "bright-smile.chat.conversation-id";
/** After this long without a first token the free-tier backend is probably waking up. */
const SLOW_START_MS = 5000;

const storage = {
  get(): string | null {
    try {
      return sessionStorage.getItem(CONVERSATION_KEY);
    } catch {
      return null;
    }
  },
  set(id: string): void {
    try {
      sessionStorage.setItem(CONVERSATION_KEY, id);
    } catch {
      // Private mode or storage disabled: the chat still works, it just won't survive a reload.
    }
  },
  clear(): void {
    try {
      sessionStorage.removeItem(CONVERSATION_KEY);
    } catch {
      // See above.
    }
  },
};

function noticeForFailure(
  status: number,
  message: string | undefined,
  retryAfter: string | null,
): ChatNotice {
  switch (status) {
    case 429:
      return { kind: "rate_limited", retryAfterSeconds: Number(retryAfter) || 60 };
    case 409:
      return { kind: "limit_reached", message: message ?? `Please call us at ${practice.phone}.` };
    case 422:
      return {
        kind: "error",
        message: "That message could not be sent. Keep it under 1,000 characters.",
      };
    default:
      return {
        kind: "error",
        message: `The assistant is not available right now. Please try again or call ${practice.phone}.`,
      };
  }
}

export function useChatSession() {
  const [state, dispatch] = useReducer(chatReducer, initialChatState);
  const [slowStart, setSlowStart] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  const send = useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!text || state.status !== "idle") {
        return;
      }
      const controller = new AbortController();
      abortRef.current = controller;
      const assistantId = crypto.randomUUID();
      dispatch({ type: "send", id: crypto.randomUUID(), text });
      const slowTimer = setTimeout(() => setSlowStart(true), SLOW_START_MS);
      let firstEvent = true;

      const attempt = async (conversationId: string | null, isRetry: boolean): Promise<void> => {
        const { data, error, response } = await api.POST("/api/chat", {
          body: { message: text, conversation_id: conversationId },
          parseAs: "stream",
          signal: controller.signal,
        });
        if (response.status === 404 && conversationId && !isRetry) {
          storage.clear(); // expired or unknown: start a fresh conversation transparently
          return attempt(null, true);
        }
        if (error || !data) {
          dispatch({
            type: "request_failed",
            text,
            notice: noticeForFailure(
              response.status,
              error?.error.message,
              response.headers.get("retry-after"),
            ),
          });
          return;
        }
        for await (const event of readChatEvents(data)) {
          if (firstEvent) {
            firstEvent = false;
            clearTimeout(slowTimer);
            setSlowStart(false);
          }
          if (event.type === "conversation") {
            storage.set(event.conversation_id);
          }
          dispatch({ type: "stream_event", event, assistantId });
        }
      };

      try {
        await attempt(storage.get(), false);
      } catch (cause) {
        if (!controller.signal.aborted) {
          dispatch({
            type: "request_failed",
            text,
            notice: {
              kind: "error",
              message: `We could not reach the assistant. Check your connection or call ${practice.phone}.`,
            },
          });
          console.error("chat request failed", cause);
        }
      } finally {
        clearTimeout(slowTimer);
        setSlowStart(false);
        dispatch({ type: "finished" });
      }
    },
    [state.status],
  );

  const dismissNotice = useCallback(() => dispatch({ type: "dismiss_notice" }), []);

  return { ...state, slowStart, send, dismissNotice };
}
