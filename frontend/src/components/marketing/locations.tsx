import { MapPinIcon } from "lucide-react";

import { phoneHref, practice } from "@/lib/practice";

function mapsHref(address: string): string {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`;
}

export function Locations() {
  return (
    <section id="locations" aria-labelledby="locations-title" className="scroll-mt-20">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-16 sm:px-6">
        <div className="flex max-w-2xl flex-col gap-3">
          <h2 id="locations-title" className="text-3xl font-bold sm:text-4xl">
            Two offices, one phone number
          </h2>
          <p className="text-muted-foreground">
            Call{" "}
            <a href={phoneHref} className="text-primary underline underline-offset-4">
              {practice.phone}
            </a>{" "}
            for either office.
          </p>
        </div>
        <div className="grid gap-10 md:grid-cols-2">
          {practice.locations.map((location) => (
            <article
              key={location.id}
              className="flex flex-col gap-4 border-t-4 border-primary pt-5"
            >
              <h3 className="text-2xl font-semibold">{location.name}</h3>
              <a
                href={mapsHref(location.address)}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-start gap-2 underline-offset-4 hover:underline"
              >
                <MapPinIcon aria-hidden className="mt-1 size-4 shrink-0 text-primary" />
                <span>
                  {location.address}
                  <span className="sr-only"> (opens Google Maps in a new tab)</span>
                </span>
              </a>
              <ul className="flex flex-col gap-1 text-muted-foreground">
                {location.hours.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
