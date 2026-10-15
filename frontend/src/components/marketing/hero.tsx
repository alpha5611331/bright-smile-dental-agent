import { AskButton } from "@/components/chat/ask-button";
import { Button } from "@/components/ui/button";
import { newPatientSpecial, phoneHref, practice } from "@/lib/practice";

/** Real questions visitors ask; each opens the assistant with that question. */
const COMMON_QUESTIONS = [
  "Do you take Cigna?",
  "How much is Invisalign?",
  "Are you open on Saturdays?",
  "What does a first visit cost?",
] as const;

export function Hero() {
  return (
    <section
      aria-labelledby="hero-title"
      className="mx-auto grid max-w-6xl gap-10 px-4 pt-12 pb-16 sm:px-6 md:grid-cols-[1fr_20rem] md:items-end md:pt-20"
    >
      <div className="flex max-w-2xl flex-col gap-6">
        <h1 id="hero-title" className="text-4xl leading-[1.05] font-bold sm:text-6xl">
          Dental care for the whole family, with prices you can see before you book.
        </h1>
        <p className="max-w-xl text-lg text-muted-foreground">
          Two offices in Montgomery County, Maryland. Bethesda is open Saturday mornings. New
          patients are welcome at both.
        </p>
        <div className="flex flex-wrap gap-3">
          <AskButton size="xl" question="I'd like to request an appointment.">
            Request a visit
          </AskButton>
          <Button variant="outline" size="xl" render={<a href={phoneHref} />}>
            Call {practice.phone}
          </Button>
        </div>
        <div className="flex flex-col gap-3 pt-2">
          <h2 className="font-sans text-sm font-medium text-muted-foreground">
            Questions people ask us
          </h2>
          <ul className="flex flex-wrap gap-2">
            {COMMON_QUESTIONS.map((question) => (
              <li key={question}>
                <AskButton
                  variant="secondary"
                  size="lg"
                  className="rounded-full"
                  question={question}
                >
                  {question}
                </AskButton>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <aside
        aria-labelledby="special-title"
        className="flex flex-col gap-3 rounded-3xl bg-accent p-6 text-accent-foreground"
      >
        <h2 id="special-title" className="text-lg font-semibold">
          New patient visit
        </h2>
        <p className="font-heading text-7xl leading-none font-bold tabular-nums">
          {newPatientSpecial.price}
        </p>
        <p>
          Exam, X-rays, and cleaning. Regularly{" "}
          <span className="tabular-nums">{newPatientSpecial.regularPrice}</span>.
        </p>
        <AskButton
          variant="outline"
          size="lg"
          className="mt-2 self-start border-accent-foreground/30 bg-transparent hover:bg-accent-foreground/10"
          question="I'm a new patient. How do I book the new patient visit?"
        >
          Book the new patient visit
        </AskButton>
      </aside>
    </section>
  );
}
