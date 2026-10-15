"use client";

import { MailIcon, PhoneIcon, TriangleAlertIcon } from "lucide-react";
import { useState } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Bubble, BubbleContent } from "@/components/ui/bubble";
import { Button } from "@/components/ui/button";
import { Field, FieldLabel } from "@/components/ui/field";
import { Message, MessageContent, MessageFooter } from "@/components/ui/message";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import {
  INTEREST_LABELS,
  LOCATION_LABELS,
  STATUS_LABELS,
  formatPhone,
  formatPracticeTime,
  type LeadDetail,
  type LeadStatus,
} from "@/lib/leads/format";
import { useLead, useUpdateLead } from "@/lib/leads/queries";
import { useNow } from "@/lib/use-now";

import { PriorityBadge, SlaIndicator } from "./lead-indicators";

const STATUS_ITEMS = (Object.entries(STATUS_LABELS) as [LeadStatus, string][]).map(
  ([value, label]) => ({ value, label }),
);

const FLAG_LABELS: Record<LeadDetail["flags"][number], string> = {
  emergency: "Emergency mentioned",
  medical_question: "Medical question asked",
};

interface LeadSheetProps {
  leadId: string | null;
  onClose: () => void;
}

export function LeadSheet({ leadId, onClose }: LeadSheetProps) {
  const { data: lead, isPending, isError } = useLead(leadId);

  return (
    <Sheet open={leadId !== null} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-full gap-0 overflow-y-auto sm:max-w-lg">
        {lead ? (
          <LeadDetails key={lead.id} lead={lead} />
        ) : (
          <SheetHeader>
            <SheetTitle>{isError ? "Lead could not be loaded" : "Loading lead"}</SheetTitle>
            <SheetDescription>
              {isError ? "Close this panel and try again." : "Fetching details and transcript."}
            </SheetDescription>
            {isPending ? (
              <div className="flex flex-col gap-3 pt-4">
                <Skeleton className="h-6 w-2/3" />
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-40 w-full" />
              </div>
            ) : null}
          </SheetHeader>
        )}
      </SheetContent>
    </Sheet>
  );
}

function LeadDetails({ lead }: { lead: LeadDetail }) {
  const update = useUpdateLead();
  const now = useNow();
  const [notes, setNotes] = useState(lead.notes);
  const notesChanged = notes.trim() !== lead.notes;

  return (
    <>
      <SheetHeader className="gap-2 border-b pb-4">
        <div className="flex flex-wrap items-center gap-2">
          <PriorityBadge priority={lead.priority} />
          <SlaIndicator lead={lead} now={now} />
        </div>
        <SheetTitle className="font-heading text-2xl">{lead.name}</SheetTitle>
        <SheetDescription>
          {INTEREST_LABELS[lead.interest]} request from the{" "}
          {lead.source === "chat" ? "chat" : "form"}, received {formatPracticeTime(lead.created_at)}
          {lead.after_hours ? " (after hours)" : ""}.
        </SheetDescription>
      </SheetHeader>

      <div className="flex flex-col gap-6 p-4">
        <div className="grid grid-cols-2 gap-2">
          <Button size="xl" render={<a href={`tel:${lead.phone}`} />}>
            <PhoneIcon data-icon="inline-start" />
            {formatPhone(lead.phone)}
          </Button>
          <Button size="xl" variant="outline" render={<a href={`mailto:${lead.email}`} />}>
            <MailIcon data-icon="inline-start" />
            Email
          </Button>
        </div>

        {lead.flags.length > 0 ? (
          <Alert variant="destructive">
            <TriangleAlertIcon />
            <AlertTitle>Review before calling</AlertTitle>
            <AlertDescription>
              <ul className="flex flex-wrap gap-2 pt-1">
                {lead.flags.map((flag) => (
                  <li key={flag}>
                    <Badge variant="destructive">{FLAG_LABELS[flag]}</Badge>
                  </li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        ) : null}

        <dl className="grid grid-cols-[8rem_1fr] gap-x-4 gap-y-2 text-sm">
          <dt className="text-muted-foreground">Reason</dt>
          <dd>{lead.reason}</dd>
          <dt className="text-muted-foreground">Office</dt>
          <dd>{LOCATION_LABELS[lead.preferred_location]}</dd>
          <dt className="text-muted-foreground">Patient</dt>
          <dd className="capitalize">
            {lead.patient_type === "unknown" ? "Not sure" : lead.patient_type}
          </dd>
          <dt className="text-muted-foreground">Email</dt>
          <dd className="break-all">{lead.email}</dd>
          {lead.contacted_at ? (
            <>
              <dt className="text-muted-foreground">First contact</dt>
              <dd>{formatPracticeTime(lead.contacted_at)}</dd>
            </>
          ) : null}
        </dl>

        <Field>
          <FieldLabel htmlFor="lead-status">Status</FieldLabel>
          <Select
            items={STATUS_ITEMS}
            value={lead.status}
            onValueChange={(status) => status && update.mutate({ id: lead.id, status })}
          >
            <SelectTrigger id="lead-status" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                {STATUS_ITEMS.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </Field>

        <Field>
          <FieldLabel htmlFor="lead-notes">Notes</FieldLabel>
          <Textarea
            id="lead-notes"
            value={notes}
            maxLength={2000}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Call outcome, preferred times, anything the team should know"
          />
          <Button
            variant="outline"
            className="self-end"
            disabled={!notesChanged || update.isPending}
            onClick={() => update.mutate({ id: lead.id, notes: notes.trim() })}
          >
            Save notes
          </Button>
        </Field>

        {lead.transcript.length > 0 ? (
          <section aria-labelledby="transcript-title" className="flex flex-col gap-3">
            <Separator />
            <h3 id="transcript-title" className="font-sans text-sm font-semibold">
              Chat transcript
            </h3>
            <ol className="flex flex-col gap-3">
              {lead.transcript.map((message, index) => (
                <li key={index}>
                  <Message align={message.role === "user" ? "end" : "start"}>
                    <MessageContent>
                      <Bubble variant={message.role === "user" ? "default" : "secondary"}>
                        <BubbleContent className="whitespace-pre-wrap">
                          {message.content}
                        </BubbleContent>
                      </Bubble>
                      <MessageFooter>
                        {message.role === "user" ? lead.name : "Assistant"},{" "}
                        {formatPracticeTime(message.created_at)}
                      </MessageFooter>
                    </MessageContent>
                  </Message>
                </li>
              ))}
            </ol>
          </section>
        ) : null}
      </div>
    </>
  );
}
