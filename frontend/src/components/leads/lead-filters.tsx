"use client";

import { Field, FieldLabel } from "@/components/ui/field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
  LOCATION_LABELS,
  PRIORITY_LABELS,
  SORT_LABELS,
  type LeadSort,
  type PreferredLocation,
  type Priority,
} from "@/lib/leads/format";

import { VIEW_LABELS, type LeadFilterState, type LeadView } from "./use-lead-filters";

const ALL = "all";

function options<T extends string>(labels: Record<T, string>, allLabel?: string) {
  const items = (Object.entries(labels) as [T, string][]).map(([value, label]) => ({
    value: value as string,
    label,
  }));
  return allLabel ? [{ value: ALL, label: allLabel }, ...items] : items;
}

const PRIORITY_OPTIONS = options(PRIORITY_LABELS, "All priorities");
const LOCATION_OPTIONS = options(LOCATION_LABELS, "All offices");
const SORT_OPTIONS = options(SORT_LABELS);

interface FilterSelectProps {
  id: string;
  label: string;
  items: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
}

function FilterSelect({ id, label, items, value, onChange }: FilterSelectProps) {
  return (
    <Field className="w-full sm:w-48">
      <FieldLabel htmlFor={id} className="sr-only">
        {label}
      </FieldLabel>
      <Select items={items} value={value} onValueChange={(next) => next && onChange(next)}>
        <SelectTrigger id={id} className="w-full" aria-label={label}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            {items.map((item) => (
              <SelectItem key={item.value} value={item.value}>
                {item.label}
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>
    </Field>
  );
}

interface LeadFiltersProps {
  state: LeadFilterState;
  onChange: (changes: Partial<LeadFilterState>) => void;
}

export function LeadFilters({ state, onChange }: LeadFiltersProps) {
  return (
    <div className="flex flex-col gap-3">
      <ToggleGroup
        aria-label="Show leads"
        variant="outline"
        className="flex-wrap"
        value={[state.view]}
        onValueChange={(value) => {
          const view = value[0] as LeadView | undefined;
          if (view) onChange({ view });
        }}
      >
        {(Object.keys(VIEW_LABELS) as LeadView[]).map((view) => (
          <ToggleGroupItem key={view} value={view}>
            {VIEW_LABELS[view]}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
      <div className="flex flex-col gap-2 sm:flex-row">
        <FilterSelect
          id="filter-priority"
          label="Priority"
          items={PRIORITY_OPTIONS}
          value={state.priority ?? ALL}
          onChange={(value) => onChange({ priority: value === ALL ? null : (value as Priority) })}
        />
        <FilterSelect
          id="filter-location"
          label="Office"
          items={LOCATION_OPTIONS}
          value={state.location ?? ALL}
          onChange={(value) =>
            onChange({ location: value === ALL ? null : (value as PreferredLocation) })
          }
        />
        <FilterSelect
          id="filter-sort"
          label="Sort"
          items={SORT_OPTIONS}
          value={state.sort}
          onChange={(value) => onChange({ sort: value as LeadSort })}
        />
      </div>
    </div>
  );
}
