"use client";

import { SendHorizontalIcon } from "lucide-react";
import { useState, type FormEvent, type KeyboardEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, FieldLabel } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";

const MAX_LENGTH = 1000;

interface ChatComposerProps {
  disabled: boolean;
  restoreText: string | null;
  onSend: (text: string) => void;
}

export function ChatComposer({ disabled, restoreText, onSend }: ChatComposerProps) {
  const [text, setText] = useState("");
  const [restored, setRestored] = useState(restoreText);

  // A failed send hands the text back so nothing the visitor typed is lost. Adjusting state while
  // rendering (instead of in an effect) avoids an extra render pass.
  if (restoreText !== restored) {
    setRestored(restoreText);
    if (restoreText) {
      setText(restoreText);
    }
  }

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    if (!text.trim() || disabled) {
      return;
    }
    onSend(text);
    setText("");
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      submit(event);
    }
  };

  return (
    <form onSubmit={submit} className="flex items-end gap-2 border-t bg-background p-3">
      <Field className="flex-1">
        <FieldLabel htmlFor="chat-message" className="sr-only">
          Your message
        </FieldLabel>
        <Textarea
          id="chat-message"
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={onKeyDown}
          maxLength={MAX_LENGTH}
          rows={1}
          placeholder="Ask about prices, insurance, or a visit"
          className="max-h-32 min-h-11 resize-none text-base"
          autoComplete="off"
        />
      </Field>
      <Button type="submit" size="icon-xl" disabled={disabled || !text.trim()}>
        <SendHorizontalIcon />
        <span className="sr-only">Send</span>
      </Button>
    </form>
  );
}
