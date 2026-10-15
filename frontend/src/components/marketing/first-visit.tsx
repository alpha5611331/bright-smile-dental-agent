import { practice } from "@/lib/practice";

/** The new patient process is a real sequence, so it is the one numbered list on the page. */
export function FirstVisit() {
  return (
    <section
      id="first-visit"
      aria-labelledby="first-visit-title"
      className="scroll-mt-20 bg-secondary"
    >
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-16 sm:px-6">
        <h2 id="first-visit-title" className="text-3xl font-bold sm:text-4xl">
          Your first visit
        </h2>
        <ol className="grid gap-8 md:grid-cols-4">
          {practice.new_patient_process.map((step, index) => (
            <li key={step} className="flex flex-col gap-3">
              <span
                aria-hidden
                className="flex size-10 items-center justify-center rounded-full bg-primary font-heading text-lg font-bold text-primary-foreground"
              >
                {index + 1}
              </span>
              <p>{step}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
