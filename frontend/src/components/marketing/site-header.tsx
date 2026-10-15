import { PhoneIcon } from "lucide-react";

import { AskButton } from "@/components/chat/ask-button";
import { Button } from "@/components/ui/button";
import { phoneHref, practice } from "@/lib/practice";

const NAV = [
  { href: "#prices", label: "Prices" },
  { href: "#locations", label: "Locations" },
  { href: "#insurance", label: "Insurance" },
  { href: "#first-visit", label: "First visit" },
] as const;

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-30 border-b bg-background/90 backdrop-blur supports-backdrop-filter:bg-background/75">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-6 px-4 sm:px-6">
        <a href="#main" className="font-heading text-lg font-bold tracking-tight">
          {practice.practice_name}
        </a>
        <nav aria-label="Sections" className="hidden md:block">
          <ul className="flex gap-5 text-sm">
            {NAV.map((item) => (
              <li key={item.href}>
                <a
                  href={item.href}
                  className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
                >
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <Button
            variant="ghost"
            size="lg"
            className="hidden sm:inline-flex"
            render={<a href={phoneHref} />}
          >
            <PhoneIcon data-icon="inline-start" />
            {practice.phone}
          </Button>
          <Button
            variant="ghost"
            size="icon-lg"
            className="sm:hidden"
            render={<a href={phoneHref} />}
          >
            <PhoneIcon />
            <span className="sr-only">Call {practice.phone}</span>
          </Button>
          <AskButton size="lg" question="I'd like to request an appointment.">
            Request a visit
          </AskButton>
        </div>
      </div>
    </header>
  );
}
