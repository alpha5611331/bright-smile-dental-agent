"use client";

import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useLeadStats } from "@/lib/leads/queries";

export function StatCards() {
  const { data, isPending, isError } = useLeadStats();

  const cards = [
    { label: "New today", value: data?.new_today, hint: "Requests received since midnight" },
    {
      label: "Overdue callbacks",
      value: data?.overdue,
      hint: "Still new after the one-business-day promise",
    },
    {
      label: "High-value consults",
      value: data?.open_high_value,
      hint: "Open Invisalign, implant, and crown requests",
    },
    {
      label: "After-hours share",
      value: data ? `${Math.round(data.after_hours_share * 100)}%` : undefined,
      hint: "Requests that came in while both offices were closed",
    },
  ];

  return (
    <section aria-label="Today at a glance" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.label} size="sm">
          <CardHeader>
            <CardDescription>{card.label}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-1">
            {isPending ? (
              <Skeleton className="h-9 w-16" />
            ) : (
              <p className="font-heading text-3xl font-bold tabular-nums">
                {isError ? (
                  <span className="text-base font-normal text-muted-foreground">Unavailable</span>
                ) : (
                  card.value
                )}
              </p>
            )}
            <p className="text-xs text-muted-foreground">{card.hint}</p>
          </CardContent>
        </Card>
      ))}
    </section>
  );
}
