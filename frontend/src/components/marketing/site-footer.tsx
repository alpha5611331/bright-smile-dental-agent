import { emailHref, phoneHref, practice } from "@/lib/practice";

export function SiteFooter() {
  return (
    <footer className="bg-foreground text-background">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-12 sm:px-6 md:flex-row md:justify-between">
        <div className="flex flex-col gap-2">
          <p className="font-heading text-xl font-bold">{practice.practice_name}</p>
          <p className="max-w-sm text-background/80">
            Family and cosmetic dentistry in Montgomery County, Maryland.
          </p>
        </div>
        <address className="flex flex-col gap-1 not-italic">
          <a href={phoneHref} className="underline-offset-4 hover:underline">
            {practice.phone}
          </a>
          <a href={emailHref} className="underline-offset-4 hover:underline">
            {practice.email}
          </a>
          {practice.locations.map((location) => (
            <span key={location.id} className="text-background/80">
              {location.address}
            </span>
          ))}
        </address>
      </div>
    </footer>
  );
}
