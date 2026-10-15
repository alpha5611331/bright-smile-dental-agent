import type { Metadata } from "next";
import { Suspense } from "react";

import { LoginForm } from "@/components/leads/login-form";
import { practice } from "@/lib/practice";

export const metadata: Metadata = { title: "Staff login" };

export default function LoginPage() {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-secondary px-4">
      <div className="flex w-full max-w-sm flex-col gap-6 rounded-2xl bg-card p-8 shadow-sm ring-1 ring-border">
        <div className="flex flex-col gap-1">
          <p className="font-heading text-lg font-bold">{practice.practice_name}</p>
          <h1 className="text-2xl font-bold">Front desk</h1>
          <p className="text-muted-foreground">Log in to see and call back appointment requests.</p>
        </div>
        <Suspense>
          <LoginForm />
        </Suspense>
      </div>
    </main>
  );
}
