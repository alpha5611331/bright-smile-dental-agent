"use client";

import type { ComponentProps } from "react";

import { Button } from "@/components/ui/button";

import { useChat } from "./chat-context";

interface AskButtonProps extends Omit<ComponentProps<typeof Button>, "onClick"> {
  /** Sent to the assistant when clicked. */
  question: string;
}

/** A button anywhere on the page that opens the chat and asks a question. */
export function AskButton({ question, ...props }: AskButtonProps) {
  const { ask } = useChat();
  return <Button {...props} onClick={() => ask(question)} />;
}
