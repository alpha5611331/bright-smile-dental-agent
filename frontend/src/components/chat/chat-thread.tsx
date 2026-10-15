"use client";

import { Bubble, BubbleContent } from "@/components/ui/bubble";
import { Message, MessageContent } from "@/components/ui/message";
import {
  MessageScroller,
  MessageScrollerButton,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/ui/message-scroller";
import { Spinner } from "@/components/ui/spinner";
import type { ChatMessage, ChatStatus } from "@/lib/chat/session";

import { QuickReplies } from "./quick-replies";

interface ChatThreadProps {
  messages: ChatMessage[];
  status: ChatStatus;
  slowStart: boolean;
  onAsk: (question: string) => void;
}

export function ChatThread({ messages, status, slowStart, onAsk }: ChatThreadProps) {
  const waiting = status === "waiting";

  return (
    <MessageScrollerProvider autoScroll>
      <MessageScroller className="flex-1">
        <MessageScrollerViewport>
          <MessageScrollerContent
            role="log"
            aria-live="polite"
            aria-busy={status !== "idle"}
            aria-label="Conversation"
            className="px-4 py-5"
          >
            <MessageScrollerItem messageId="greeting">
              <Message align="start">
                <MessageContent>
                  <Bubble variant="secondary">
                    <BubbleContent>
                      Hi! I can answer questions about our services, prices, insurance, and hours,
                      and I can pass your appointment request to the front desk.
                    </BubbleContent>
                  </Bubble>
                </MessageContent>
              </Message>
            </MessageScrollerItem>

            {messages.length === 0 ? (
              <MessageScrollerItem messageId="quick-replies">
                <QuickReplies onAsk={onAsk} disabled={status !== "idle"} />
              </MessageScrollerItem>
            ) : null}

            {messages.map((message) => (
              <MessageScrollerItem
                key={message.id}
                messageId={message.id}
                scrollAnchor={message.role === "user"}
              >
                <Message align={message.role === "user" ? "end" : "start"}>
                  <MessageContent>
                    <Bubble variant={message.role === "user" ? "default" : "secondary"}>
                      <BubbleContent className="whitespace-pre-wrap">{message.text}</BubbleContent>
                    </Bubble>
                  </MessageContent>
                </Message>
              </MessageScrollerItem>
            ))}

            {waiting ? (
              <MessageScrollerItem messageId="waiting">
                <Message align="start">
                  <MessageContent>
                    <Bubble variant="secondary">
                      <BubbleContent className="flex items-center gap-2 text-muted-foreground">
                        <Spinner />
                        {slowStart
                          ? "Waking up the assistant. This can take up to a minute."
                          : "Checking our office information"}
                      </BubbleContent>
                    </Bubble>
                  </MessageContent>
                </Message>
              </MessageScrollerItem>
            ) : null}
          </MessageScrollerContent>
        </MessageScrollerViewport>
        <MessageScrollerButton />
      </MessageScroller>
    </MessageScrollerProvider>
  );
}
