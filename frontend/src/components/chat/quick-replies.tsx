"use client";

import { Button } from "@/components/ui/button";

/** First-step suggestions (SPEC section 8.2). Each sends a plain question the visitor could type. */
export const QUICK_REPLIES = [
  { label: "Book a visit", question: "I'd like to request an appointment." },
  { label: "Insurance", question: "Which insurance plans do you accept?" },
  { label: "Hours and locations", question: "Where are your offices and when are you open?" },
  { label: "Pricing", question: "How much do your services cost?" },
  { label: "Emergency", question: "I have a dental emergency. What should I do?" },
] as const;

interface QuickRepliesProps {
  onAsk: (question: string) => void;
  disabled?: boolean;
}

export function QuickReplies({ onAsk, disabled = false }: QuickRepliesProps) {
  return (
    <ul aria-label="Suggested questions" className="flex flex-wrap gap-2">
      {QUICK_REPLIES.map((reply) => (
        <li key={reply.label}>
          <Button
            variant="outline"
            size="lg"
            className="rounded-full"
            disabled={disabled}
            onClick={() => onAsk(reply.question)}
          >
            {reply.label}
          </Button>
        </li>
      ))}
    </ul>
  );
}
