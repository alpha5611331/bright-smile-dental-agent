import { CheckIcon } from "lucide-react";

import { practice } from "@/lib/practice";

const { in_network: inNetwork, not_accepted: notAccepted } = practice.insurance;

export function Insurance() {
  return (
    <section id="insurance" aria-labelledby="insurance-title" className="scroll-mt-20 border-t">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 md:grid-cols-[18rem_1fr]">
        <div className="flex flex-col gap-3">
          <h2 id="insurance-title" className="text-3xl font-bold sm:text-4xl">
            Insurance
          </h2>
          <p className="text-muted-foreground">
            We are in network with these plans. We do not accept {notAccepted.join(" or ")}.
          </p>
        </div>
        <ul className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
          {inNetwork.map((plan) => (
            <li key={plan} className="flex items-center gap-3 text-lg">
              <CheckIcon aria-hidden className="size-5 shrink-0 text-primary" />
              {plan}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
