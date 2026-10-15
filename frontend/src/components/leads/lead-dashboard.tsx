"use client";

import { useQueryClient } from "@tanstack/react-query";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { LOGIN_PATH, setUnauthorizedHandler } from "@/lib/leads/queries";

import { DashboardHeader } from "./dashboard-header";
import { LeadFilters } from "./lead-filters";
import { LeadSheet } from "./lead-sheet";
import { LeadsTable } from "./leads-table";
import { StatCards } from "./stat-cards";
import { useLeadFilters } from "./use-lead-filters";

export function LeadDashboard() {
  const { state, filters, update } = useLeadFilters();
  const [openLeadId, setOpenLeadId] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  // An expired session: drop cached patient data and return to login, then come back here.
  useEffect(
    () =>
      setUnauthorizedHandler(() => {
        queryClient.clear();
        const query = searchParams.toString();
        const next = encodeURIComponent(query ? `${pathname}?${query}` : pathname);
        router.replace(`${LOGIN_PATH}?next=${next}`);
      }),
    [pathname, queryClient, router, searchParams],
  );

  return (
    <div className="min-h-dvh bg-background">
      <DashboardHeader />
      <main className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6">
        <h1 className="sr-only">Appointment requests</h1>
        <StatCards />
        <section aria-labelledby="leads-title" className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <h2 id="leads-title" className="text-2xl font-bold">
              Callback list
            </h2>
            <p className="text-sm text-muted-foreground">
              Highest priority first. Every request should get a call within one business day.
            </p>
          </div>
          <LeadFilters state={state} onChange={update} />
          <LeadsTable
            filters={filters}
            onOpenLead={setOpenLeadId}
            onPageChange={(page) => update({ page })}
            onShowAll={() => update({ view: "all", priority: null, location: null })}
          />
        </section>
      </main>
      <LeadSheet leadId={openLeadId} onClose={() => setOpenLeadId(null)} />
    </div>
  );
}
