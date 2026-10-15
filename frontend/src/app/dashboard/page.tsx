import { Suspense } from "react";

import { LeadDashboard } from "@/components/leads/lead-dashboard";

export default function DashboardPage() {
  // Filters are read from the URL on the client, which requires a Suspense boundary.
  return (
    <Suspense>
      <LeadDashboard />
    </Suspense>
  );
}
