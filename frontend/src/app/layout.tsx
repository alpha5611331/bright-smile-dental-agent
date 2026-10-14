import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";

import { cn } from "@/lib/utils";

import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: {
    default: "Bright Smile Dental | Family and Cosmetic Dentistry in Bethesda and Rockville",
    template: "%s | Bright Smile Dental",
  },
  description:
    "Family and cosmetic dental care in Montgomery County, Maryland. New patients welcome at our Bethesda and Rockville offices.",
  applicationName: "Bright Smile Dental",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={cn("font-sans antialiased", geist.variable)}>
      <body className="min-h-dvh bg-background text-foreground">{children}</body>
    </html>
  );
}
