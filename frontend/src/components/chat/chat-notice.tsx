"use client";

import { CircleCheckIcon, InfoIcon, TriangleAlertIcon } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import type { ChatNotice as Notice } from "@/lib/chat/session";
import { phoneHref, practice } from "@/lib/practice";

function CallLink() {
  return (
    <a href={phoneHref} className="font-medium text-primary underline underline-offset-4">
      {practice.phone}
    </a>
  );
}

export function ChatNotice({ notice }: { notice: Notice }) {
  switch (notice.kind) {
    case "lead_captured":
      return (
        <Alert>
          <CircleCheckIcon />
          <AlertTitle>Request received</AlertTitle>
          <AlertDescription>
            Our front desk will call you within one business day to schedule.
          </AlertDescription>
        </Alert>
      );
    case "rate_limited":
      return (
        <Alert>
          <InfoIcon />
          <AlertTitle>Slow down a little</AlertTitle>
          <AlertDescription>
            You can send another message in {notice.retryAfterSeconds} seconds.
          </AlertDescription>
        </Alert>
      );
    case "limit_reached":
      return (
        <Alert>
          <InfoIcon />
          <AlertTitle>This chat is full</AlertTitle>
          <AlertDescription>
            <p>
              Please call us at <CallLink />, or reload the page to start a new chat.
            </p>
          </AlertDescription>
        </Alert>
      );
    case "error":
      return (
        <Alert variant="destructive">
          <TriangleAlertIcon />
          <AlertTitle>Message not answered</AlertTitle>
          <AlertDescription>
            <p>{notice.message}</p>
          </AlertDescription>
        </Alert>
      );
  }
}
