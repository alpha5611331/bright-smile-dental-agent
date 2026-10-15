"use client";

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
  type QueryKey,
} from "@tanstack/react-query";
import createClient from "openapi-fetch";
import { toast } from "sonner";

import type { paths } from "@/lib/api/schema";

import {
  STATUS_LABELS,
  type Lead,
  type LeadDetail,
  type LeadPage,
  type LeadSort,
  type LeadStatus,
  type PreferredLocation,
  type Priority,
} from "./format";

export const LOGIN_PATH = "/dashboard/login";

let unauthorizedHandler: (() => void) | null = null;

/**
 * Register what happens when the session expires (a 401 from any staff request). The dashboard
 * registers a router redirect to the login page. Returns an unregister function.
 */
export function setUnauthorizedHandler(handler: () => void): () => void {
  unauthorizedHandler = handler;
  return () => {
    if (unauthorizedHandler === handler) {
      unauthorizedHandler = null;
    }
  };
}

/** Staff API client: every response is checked for an expired session. */
export const staffApi = createClient<paths>({ baseUrl: "" });
staffApi.use({
  onResponse({ response }) {
    if (response.status === 401) {
      unauthorizedHandler?.();
    }
    return response;
  },
});

export interface LeadFilters {
  status: LeadStatus[];
  priority: Priority[];
  location: PreferredLocation | null;
  sort: LeadSort;
  page: number;
}

export const PAGE_SIZE = 25;

export const queryKeys = {
  leads: ["leads"] as const,
  leadList: (filters: LeadFilters) => ["leads", "list", filters] as const,
  lead: (id: string) => ["leads", "detail", id] as const,
  stats: ["stats"] as const,
};

class ApiRequestError extends Error {}

function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.data === undefined) {
    throw new ApiRequestError(`Request failed with status ${result.response.status}`);
  }
  return result.data;
}

export function useLeads(filters: LeadFilters) {
  return useQuery({
    queryKey: queryKeys.leadList(filters),
    queryFn: async ({ signal }) =>
      unwrap(
        await staffApi.GET("/api/leads", {
          params: {
            query: {
              status: filters.status.length ? filters.status : undefined,
              priority: filters.priority.length ? filters.priority : undefined,
              location: filters.location ?? undefined,
              sort: filters.sort,
              page: filters.page,
              page_size: PAGE_SIZE,
            },
          },
          signal,
        }),
      ),
    placeholderData: keepPreviousData,
  });
}

export function useLeadStats() {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: async ({ signal }) => unwrap(await staffApi.GET("/api/stats", { signal })),
  });
}

export function useLead(id: string | null) {
  return useQuery({
    queryKey: queryKeys.lead(id ?? ""),
    queryFn: async ({ signal }) =>
      unwrap(
        await staffApi.GET("/api/leads/{lead_id}", {
          params: { path: { lead_id: id ?? "" } },
          signal,
        }),
      ),
    enabled: id !== null,
  });
}

export interface LeadUpdate {
  id: string;
  status?: LeadStatus;
  notes?: string;
}

type Snapshot = [QueryKey, unknown][];

/** Status and notes edits apply instantly and roll back if the server rejects them (SPEC US-5). */
export function useUpdateLead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...body }: LeadUpdate) =>
      unwrap(
        await staffApi.PATCH("/api/leads/{lead_id}", {
          params: { path: { lead_id: id } },
          body,
        }),
      ),
    onMutate: async ({ id, ...changes }): Promise<{ snapshot: Snapshot }> => {
      await queryClient.cancelQueries({ queryKey: queryKeys.leads });
      const snapshot: Snapshot = queryClient.getQueriesData({ queryKey: queryKeys.leads });
      const apply = <T extends Lead>(lead: T): T =>
        lead.id === id
          ? {
              ...lead,
              ...changes,
              overdue: changes.status && changes.status !== "new" ? false : lead.overdue,
            }
          : lead;
      queryClient.setQueriesData<LeadPage>({ queryKey: [...queryKeys.leads, "list"] }, (page) =>
        page ? { ...page, items: page.items.map(apply) } : page,
      );
      queryClient.setQueryData<LeadDetail>(queryKeys.lead(id), (detail) =>
        detail ? apply(detail) : detail,
      );
      return { snapshot };
    },
    onError: (_error, _variables, context) => {
      for (const [key, data] of context?.snapshot ?? []) {
        queryClient.setQueryData(key, data);
      }
      toast.error("The change was not saved. Please try again.");
    },
    onSuccess: (lead, variables) => {
      toast.success(
        variables.status ? `Marked as ${STATUS_LABELS[lead.status].toLowerCase()}` : "Notes saved",
      );
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.leads });
      void queryClient.invalidateQueries({ queryKey: queryKeys.stats });
    },
  });
}
