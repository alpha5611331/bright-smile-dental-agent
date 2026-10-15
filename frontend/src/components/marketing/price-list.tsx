import { practice, splitPrice } from "@/lib/practice";

/**
 * The page's one bold element: published prices set like a menu board, with dotted leaders
 * running from each service to its price.
 */
export function PriceList() {
  return (
    <section id="prices" aria-labelledby="prices-title" className="scroll-mt-20 border-t">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 md:grid-cols-[18rem_1fr]">
        <div className="flex flex-col gap-3">
          <h2 id="prices-title" className="text-3xl font-bold sm:text-4xl">
            Our prices
          </h2>
          <p className="text-muted-foreground">{practice.pricing_note}</p>
        </div>
        <dl className="flex flex-col">
          {practice.services.map((service) => {
            const { amount, note } = splitPrice(service.price);
            return (
              <div
                key={service.name}
                className="flex flex-col gap-1 border-b border-border/70 py-4 sm:flex-row sm:items-baseline sm:gap-3"
              >
                <dt className="flex flex-col">
                  <span className="text-lg font-medium">{service.name}</span>
                  {note ? <span className="text-sm text-muted-foreground">{note}</span> : null}
                </dt>
                <span
                  aria-hidden
                  className="hidden min-w-8 flex-1 self-baseline border-b-2 border-dotted border-input sm:block"
                />
                <dd className="font-heading text-xl font-semibold text-primary tabular-nums sm:text-right">
                  {amount}
                </dd>
              </div>
            );
          })}
        </dl>
      </div>
    </section>
  );
}
