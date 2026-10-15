import { PhoneIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { emergencyGuidance, phoneHref, practice } from "@/lib/practice";

export function Emergencies() {
  return (
    <section aria-labelledby="emergencies-title" className="border-t">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-16 sm:px-6 md:grid-cols-[18rem_1fr]">
        <div className="flex flex-col gap-4">
          <h2 id="emergencies-title" className="text-3xl font-bold sm:text-4xl">
            Dental emergencies
          </h2>
          <Button size="xl" className="self-start" render={<a href={phoneHref} />}>
            <PhoneIcon data-icon="inline-start" />
            Call {practice.phone}
          </Button>
        </div>
        <ul className="flex flex-col gap-4 text-lg">
          {emergencyGuidance.map((line) => (
            <li key={line} className="border-l-4 border-accent pl-4">
              {line}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
