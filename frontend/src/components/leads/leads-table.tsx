"use client";

import { InboxIcon, RefreshCwIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  INTEREST_LABELS,
  LOCATION_LABELS,
  STATUS_LABELS,
  formatAgo,
  formatPracticeTime,
  type Lead,
} from "@/lib/leads/format";
import { PAGE_SIZE, useLeads, type LeadFilters } from "@/lib/leads/queries";
import { cn } from "@/lib/utils";
import { useNow } from "@/lib/use-now";

import { PriorityBadge, SlaIndicator } from "./lead-indicators";

interface LeadsTableProps {
  filters: LeadFilters;
  onOpenLead: (id: string) => void;
  onPageChange: (page: number) => void;
  onShowAll: () => void;
}

export function LeadsTable({ filters, onOpenLead, onPageChange, onShowAll }: LeadsTableProps) {
  const { data, isPending, isError, isFetching, refetch } = useLeads(filters);
  const now = useNow();

  if (isError) {
    return (
      <Empty className="border">
        <EmptyHeader>
          <EmptyTitle>Leads could not be loaded</EmptyTitle>
          <EmptyDescription>
            The server did not respond. Check the connection and retry.
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button variant="outline" onClick={() => void refetch()}>
            <RefreshCwIcon data-icon="inline-start" />
            Retry
          </Button>
        </EmptyContent>
      </Empty>
    );
  }

  if (!isPending && data.items.length === 0) {
    return (
      <Empty className="border">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <InboxIcon />
          </EmptyMedia>
          <EmptyTitle>No leads here</EmptyTitle>
          <EmptyDescription>
            Nothing matches these filters. New requests from the website appear here automatically.
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button variant="outline" onClick={onShowAll}>
            Show all leads
          </Button>
        </EmptyContent>
      </Empty>
    );
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="flex flex-col gap-3">
      <div
        className={cn(
          "rounded-xl border transition-opacity",
          isFetching && !isPending && "opacity-70",
        )}
      >
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-28">Priority</TableHead>
              <TableHead>Patient</TableHead>
              <TableHead className="hidden md:table-cell">Office</TableHead>
              <TableHead className="hidden lg:table-cell">Received</TableHead>
              <TableHead>Callback</TableHead>
              <TableHead className="hidden sm:table-cell">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isPending
              ? Array.from({ length: 6 }, (_, index) => (
                  <TableRow key={index}>
                    {Array.from({ length: 6 }, (__, cell) => (
                      <TableCell key={cell}>
                        <Skeleton className="h-5 w-full max-w-32" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              : data.items.map((lead) => (
                  <LeadRow key={lead.id} lead={lead} now={now} onOpen={() => onOpenLead(lead.id)} />
                ))}
          </TableBody>
        </Table>
      </div>
      {data && data.total > PAGE_SIZE ? (
        <nav aria-label="Pages" className="flex items-center justify-between gap-3 text-sm">
          <span className="text-muted-foreground">
            Page {filters.page} of {totalPages} ({data.total} leads)
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={filters.page <= 1}
              onClick={() => onPageChange(filters.page - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={filters.page >= totalPages}
              onClick={() => onPageChange(filters.page + 1)}
            >
              Next
            </Button>
          </div>
        </nav>
      ) : null}
    </div>
  );
}

function LeadRow({ lead, now, onOpen }: { lead: Lead; now: Date; onOpen: () => void }) {
  return (
    <TableRow
      className={cn("cursor-pointer", lead.overdue && "bg-destructive/5 hover:bg-destructive/10")}
      onClick={onOpen}
    >
      <TableCell>
        <PriorityBadge priority={lead.priority} short />
      </TableCell>
      <TableCell>
        {/* The name is the row's keyboard target; the whole row is clickable for pointer users. */}
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onOpen();
          }}
          className="flex flex-col items-start text-left font-medium underline-offset-4 outline-none hover:underline focus-visible:underline focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          {lead.name}
          <span className="text-xs font-normal text-muted-foreground">
            {INTEREST_LABELS[lead.interest]}
            {lead.after_hours ? ", after hours" : ""}
          </span>
        </button>
      </TableCell>
      <TableCell className="hidden md:table-cell">
        {LOCATION_LABELS[lead.preferred_location]}
      </TableCell>
      <TableCell className="hidden lg:table-cell" title={formatPracticeTime(lead.created_at)}>
        {formatAgo(lead.created_at, now)}
      </TableCell>
      <TableCell className="whitespace-normal sm:whitespace-nowrap">
        <SlaIndicator lead={lead} now={now} />
      </TableCell>
      <TableCell className="hidden sm:table-cell">{STATUS_LABELS[lead.status]}</TableCell>
    </TableRow>
  );
}
