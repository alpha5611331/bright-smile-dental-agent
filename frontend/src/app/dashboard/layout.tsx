import type { Metadata } from "next";

import { DashboardProviders } from "@/components/providers";

export const metadata: Metadata = {
  title: "Front desk",
  robots: { index: false, follow: false },
};

export default function DashboardLayout({ children }: LayoutProps<"/dashboard">) {
  return <DashboardProviders>{children}</DashboardProviders>;
}
