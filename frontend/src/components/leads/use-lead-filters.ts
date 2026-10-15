"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import {
  LOCATION_LABELS,
  OPEN_STATUSES,
  PRIORITY_LABELS,
  SORT_LABELS,
  STATUS_LABELS,
  type LeadSort,
  type LeadStatus,
  type PreferredLocation,
  type Priority,
} from "@/lib/leads/format";
import type { LeadFilters } from "@/lib/leads/queries";

/** The status tabs. "open" is the default triage view: everything still waiting on the front desk. */
export type LeadView = "open" | "all" | LeadStatus;

export const VIEW_LABELS: Record<LeadView, string> = {
  open: "Open",
  ...STATUS_LABELS,
  all: "All",
};

function isKey<T extends string>(labels: Record<T, string>, value: string | null): value is T {
  return value !== null && Object.hasOwn(labels, value);
}

export interface LeadFilterState {
  view: LeadView;
  priority: Priority | null;
  location: PreferredLocation | null;
  sort: LeadSort;
  page: number;
}

/** Filters live in the URL so a view survives a reload and can be shared with a colleague. */
export function useLeadFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const state = useMemo<LeadFilterState>(() => {
    const view = searchParams.get("view");
    const priority = searchParams.get("priority");
    const location = searchParams.get("location");
    const sort = searchParams.get("sort");
    const page = Number(searchParams.get("page"));
    return {
      view: isKey(VIEW_LABELS, view) ? view : "open",
      priority: isKey(PRIORITY_LABELS, priority) ? priority : null,
      location: isKey(LOCATION_LABELS, location) ? location : null,
      sort: isKey(SORT_LABELS, sort) ? sort : "priority",
      page: Number.isInteger(page) && page > 0 ? page : 1,
    };
  }, [searchParams]);

  const filters = useMemo<LeadFilters>(
    () => ({
      status: state.view === "open" ? [...OPEN_STATUSES] : state.view === "all" ? [] : [state.view],
      priority: state.priority ? [state.priority] : [],
      location: state.location,
      sort: state.sort,
      page: state.page,
    }),
    [state],
  );

  const update = useCallback(
    (changes: Partial<LeadFilterState>) => {
      const next = { ...state, page: 1, ...changes };
      const params = new URLSearchParams();
      if (next.view !== "open") params.set("view", next.view);
      if (next.priority) params.set("priority", next.priority);
      if (next.location) params.set("location", next.location);
      if (next.sort !== "priority") params.set("sort", next.sort);
      if (next.page > 1) params.set("page", String(next.page));
      const query = params.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [pathname, router, state],
  );

  return { state, filters, update };
}
