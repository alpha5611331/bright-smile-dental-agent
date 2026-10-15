import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque, Lexend } from "next/font/google";

import { Toaster } from "@/components/ui/sonner";
import { cn } from "@/lib/utils";

import "./globals.css";

const bodyFont = Lexend({ subsets: ["latin"], variable: "--font-sans" });
const displayFont = Bricolage_Grotesque({ subsets: ["latin"], variable: "--font-display" });

export const metadata: Metadata = {
  title: {
    default: "Bright Smile Dental | Family and cosmetic dentistry in Bethesda and Rockville",
    template: "%s | Bright Smile Dental",
  },
  description:
    "Family and cosmetic dental care in Montgomery County, Maryland. Published prices, a $149 new patient visit, and offices in Bethesda and Rockville.",
  applicationName: "Bright Smile Dental",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f7f8f5",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={cn("font-sans antialiased", bodyFont.variable, displayFont.variable)}
    >
      <body className="min-h-dvh bg-background text-foreground">
        {children}
        <Toaster />
      </body>
    </html>
  );
}
