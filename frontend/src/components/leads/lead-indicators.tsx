import { AlarmClockIcon, CircleCheckIcon, ClockIcon } from "lucide-react";
import type { ComponentProps } from "react";

import { Badge } from "@/components/ui/badge";
import { PRIORITY_LABELS, slaStatus, type Lead, type Priority } from "@/lib/leads/format";
import { cn } from "@/lib/utils";

const PRIORITY_VARIANT: Record<Priority, ComponentProps<typeof Badge>["variant"]> = {
  P1: "destructive",
  P2: "accent",
  P3: "default",
  P4: "secondary",
};

export function PriorityBadge({
  priority,
  short = false,
}: {
  priority: Priority;
  short?: boolean;
}) {
  return (
    <Badge variant={PRIORITY_VARIANT[priority]} title={PRIORITY_LABELS[priority]}>
      {short ? priority : PRIORITY_LABELS[priority]}
    </Badge>
  );
}

export function SlaIndicator({
  lead,
  now,
}: {
  lead: Pick<Lead, "status" | "sla_due_at">;
  now: Date;
}) {
  const { tone, label } = slaStatus(lead, now);
  const Icon =
    tone === "closed" ? CircleCheckIcon : tone === "on_track" ? ClockIcon : AlarmClockIcon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-sm sm:whitespace-nowrap",
        tone === "overdue" && "font-semibold text-destructive",
        tone === "due_soon" && "font-medium text-foreground",
        (tone === "on_track" || tone === "closed") && "text-muted-foreground",
      )}
    >
      <Icon aria-hidden className="size-4 shrink-0" />
      {label}
    </span>
  );
}
