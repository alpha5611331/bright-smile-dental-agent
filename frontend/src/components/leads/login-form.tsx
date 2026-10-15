"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { api } from "@/lib/api/client";

/** Only same-site dashboard paths are valid redirect targets (no open redirects). */
function safeNext(next: string | null): string {
  return next && next.startsWith("/dashboard") && !next.startsWith("//") ? next : "/dashboard";
}

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const { response } = await api.POST("/api/auth/login", { body: { password } });
      if (response.ok) {
        router.replace(safeNext(searchParams.get("next")));
        return;
      }
      setError(
        response.status === 429
          ? `Too many attempts. Try again in ${response.headers.get("retry-after") ?? "a few"} seconds.`
          : "That password is not correct.",
      );
    } catch {
      setError("Could not reach the server. Check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-5">
      <FieldGroup>
        <Field data-invalid={error ? true : undefined}>
          <FieldLabel htmlFor="staff-password">Staff password</FieldLabel>
          <Input
            id="staff-password"
            type="password"
            autoComplete="current-password"
            required
            autoFocus
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-invalid={error ? true : undefined}
            className="h-11 text-base"
          />
        </Field>
      </FieldGroup>
      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}
      <Button type="submit" size="xl" disabled={submitting || !password}>
        {submitting ? <Spinner data-icon="inline-start" /> : null}
        Log in
      </Button>
    </form>
  );
}
