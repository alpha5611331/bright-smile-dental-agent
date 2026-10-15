"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type LeadCreate = components["schemas"]["LeadCreate"];

const LOCATIONS = [
  { value: "no_preference", label: "No preference" },
  { value: "bethesda", label: "Bethesda" },
  { value: "rockville", label: "Rockville" },
] as const satisfies readonly { value: LeadCreate["preferred_location"]; label: string }[];

const PATIENT_TYPES = [
  { value: "new", label: "New patient" },
  { value: "existing", label: "Existing patient" },
] as const satisfies readonly { value: NonNullable<LeadCreate["patient_type"]>; label: string }[];

/** Mirrors the server rules for instant feedback; the server remains the authority. */
const leadSchema = z.object({
  name: z.string().trim().min(1, "Enter your name.").max(100),
  phone: z
    .string()
    .trim()
    .refine((value) => value.replace(/\D/g, "").length >= 10, "Enter a US phone number."),
  email: z.email("Enter a valid email address."),
  reason: z.string().trim().min(1, "Tell us what the visit is for.").max(500),
  preferred_location: z.enum(["no_preference", "bethesda", "rockville"]),
  patient_type: z.enum(["new", "existing"]),
  contact_consent: z.literal(true, "We need your permission to call you."),
});

type FormValues = z.input<typeof leadSchema>;
type FieldName = keyof FormValues;
type FieldErrors = Partial<Record<FieldName, string>>;

const EMPTY: FormValues = {
  name: "",
  phone: "",
  email: "",
  reason: "",
  preferred_location: "no_preference",
  patient_type: "new",
  contact_consent: false as unknown as true,
};

interface LeadFormProps {
  onSubmitted: () => void;
  onCancel: () => void;
}

export function LeadForm({ onSubmitted, onCancel }: LeadFormProps) {
  const [values, setValues] = useState<FormValues>(EMPTY);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);

  const update = <K extends FieldName>(key: K, value: FormValues[K]) => {
    setValues((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: undefined }));
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const parsed = leadSchema.safeParse(values);
    if (!parsed.success) {
      setErrors(
        Object.fromEntries(parsed.error.issues.map((issue) => [issue.path[0], issue.message])),
      );
      return;
    }
    setSubmitting(true);
    try {
      const { error, response } = await api.POST("/api/leads", { body: parsed.data });
      if (response.ok) {
        toast.success("Request sent. Our front desk will call you within one business day.");
        onSubmitted();
        return;
      }
      if (response.status === 422 && error && "error" in error) {
        const serverErrors: FieldErrors = {};
        for (const detail of error.error.details ?? []) {
          const field = detail.loc[1];
          if (typeof field === "string" && field in EMPTY) {
            serverErrors[field as FieldName] = detail.msg.replace(/^Value error, /, "");
          }
        }
        setErrors(serverErrors);
        return;
      }
      toast.error(
        response.status === 429
          ? "Too many requests from this device. Please try again later or call us."
          : "Your request was not sent. Please try again or call us.",
      );
    } catch {
      toast.error("Your request was not sent. Check your connection or call us.");
    } finally {
      setSubmitting(false);
    }
  };

  const invalid = (field: FieldName) => Boolean(errors[field]);

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-1 flex-col gap-5 overflow-y-auto p-4">
      <p className="text-muted-foreground">
        Leave your details and the front desk will call you within one business day.
      </p>
      <FieldGroup>
        <Field data-invalid={invalid("name") || undefined}>
          <FieldLabel htmlFor="lead-name">Full name</FieldLabel>
          <Input
            id="lead-name"
            autoComplete="name"
            value={values.name}
            onChange={(e) => update("name", e.target.value)}
            aria-invalid={invalid("name") || undefined}
          />
          <FieldError>{errors.name}</FieldError>
        </Field>
        <Field data-invalid={invalid("phone") || undefined}>
          <FieldLabel htmlFor="lead-phone">Phone</FieldLabel>
          <Input
            id="lead-phone"
            type="tel"
            autoComplete="tel"
            value={values.phone}
            onChange={(e) => update("phone", e.target.value)}
            aria-invalid={invalid("phone") || undefined}
          />
          <FieldError>{errors.phone}</FieldError>
        </Field>
        <Field data-invalid={invalid("email") || undefined}>
          <FieldLabel htmlFor="lead-email">Email</FieldLabel>
          <Input
            id="lead-email"
            type="email"
            autoComplete="email"
            value={values.email}
            onChange={(e) => update("email", e.target.value)}
            aria-invalid={invalid("email") || undefined}
          />
          <FieldError>{errors.email}</FieldError>
        </Field>
        <Field data-invalid={invalid("reason") || undefined}>
          <FieldLabel htmlFor="lead-reason">What is the visit for?</FieldLabel>
          <Textarea
            id="lead-reason"
            maxLength={500}
            value={values.reason}
            onChange={(e) => update("reason", e.target.value)}
            aria-invalid={invalid("reason") || undefined}
          />
          <FieldError>{errors.reason}</FieldError>
        </Field>
        <Field>
          <FieldLabel htmlFor="lead-location">Preferred office</FieldLabel>
          <Select
            items={LOCATIONS}
            value={values.preferred_location}
            onValueChange={(value) => value && update("preferred_location", value)}
          >
            <SelectTrigger id="lead-location" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                {LOCATIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </Field>
        <Field>
          <FieldLabel htmlFor="lead-patient-type">Have you visited us before?</FieldLabel>
          <Select
            items={PATIENT_TYPES}
            value={values.patient_type}
            onValueChange={(value) => value && update("patient_type", value)}
          >
            <SelectTrigger id="lead-patient-type" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                {PATIENT_TYPES.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </Field>
        <Field orientation="horizontal" data-invalid={invalid("contact_consent") || undefined}>
          <Checkbox
            id="lead-consent"
            checked={values.contact_consent === true}
            onCheckedChange={(checked) =>
              update("contact_consent", (checked === true) as unknown as true)
            }
            aria-invalid={invalid("contact_consent") || undefined}
          />
          <FieldLabel htmlFor="lead-consent" className="font-normal">
            Bright Smile Dental may call or email me about this request.
          </FieldLabel>
        </Field>
        <FieldError>{errors.contact_consent}</FieldError>
      </FieldGroup>
      <div className="mt-auto flex gap-2">
        <Button type="submit" size="xl" className="flex-1" disabled={submitting}>
          {submitting ? <Spinner data-icon="inline-start" /> : null}
          Send request
        </Button>
        <Button type="button" variant="ghost" size="xl" onClick={onCancel}>
          Back to chat
        </Button>
      </div>
    </form>
  );
}
