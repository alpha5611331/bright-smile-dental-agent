"use client";

import { MessageCircleIcon } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { phoneHref, practice } from "@/lib/practice";

import { useChat } from "./chat-context";
import { ChatComposer } from "./chat-composer";
import { ChatNotice } from "./chat-notice";
import { ChatThread } from "./chat-thread";
import { LeadForm } from "./lead-form";

type View = "chat" | "form";

export function ChatWidget() {
  const { open, setOpen, session } = useChat();
  const [view, setView] = useState<View>("chat");

  return (
    <>
      <Button
        size="xl"
        className="fixed right-4 bottom-4 z-40 rounded-full shadow-lg sm:right-6 sm:bottom-6"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
      >
        <MessageCircleIcon data-icon="inline-start" />
        Ask us a question
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="inset-0 flex h-dvh max-w-none translate-x-0 translate-y-0 flex-col gap-0 rounded-none p-0 sm:inset-auto sm:right-6 sm:bottom-6 sm:h-[min(42rem,calc(100dvh-3rem))] sm:w-[26rem] sm:max-w-none sm:rounded-2xl">
          <header className="border-b px-4 pt-4 pr-12 pb-3">
            <DialogTitle className="font-heading text-lg">Ask Bright Smile Dental</DialogTitle>
            <DialogDescription>
              Answers come from our office information. Prefer to talk?{" "}
              <a href={phoneHref} className="text-primary underline underline-offset-4">
                Call {practice.phone}
              </a>
              .
            </DialogDescription>
          </header>

          {view === "chat" ? (
            <>
              <ChatThread
                messages={session.messages}
                status={session.status}
                slowStart={session.slowStart}
                onAsk={(question) => void session.send(question)}
              />
              {session.notice ? (
                <div className="px-3 pb-2">
                  <ChatNotice notice={session.notice} />
                </div>
              ) : null}
              <ChatComposer
                disabled={session.status !== "idle"}
                restoreText={session.retryText}
                onSend={(text) => void session.send(text)}
              />
              <footer className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 px-4 pb-3 text-xs text-muted-foreground">
                <p>
                  AI assistant, not medical advice. In an emergency, call {practice.phone} or go to
                  the nearest emergency room.
                </p>
                <Button variant="link" size="sm" className="px-0" onClick={() => setView("form")}>
                  Prefer a form?
                </Button>
              </footer>
            </>
          ) : (
            <LeadForm onSubmitted={() => setOpen(false)} onCancel={() => setView("chat")} />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
