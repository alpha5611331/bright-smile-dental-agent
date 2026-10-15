"use client";

import { createContext, use, useCallback, useMemo, useState, type ReactNode } from "react";

import { useChatSession } from "./use-chat-session";

type ChatSession = ReturnType<typeof useChatSession>;

interface ChatContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
  /** Open the chat and send a question, e.g. from a suggestion on the page. */
  ask: (question: string) => void;
  session: ChatSession;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const session = useChatSession();
  const { send } = session;

  const ask = useCallback(
    (question: string) => {
      setOpen(true);
      void send(question);
    },
    [send],
  );

  const value = useMemo(() => ({ open, setOpen, ask, session }), [open, ask, session]);
  return <ChatContext value={value}>{children}</ChatContext>;
}

export function useChat(): ChatContextValue {
  const context = use(ChatContext);
  if (!context) {
    throw new Error("useChat must be used inside <ChatProvider>");
  }
  return context;
}
