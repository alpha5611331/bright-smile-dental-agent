import { AskButton } from "@/components/chat/ask-button";
import { practice } from "@/lib/practice";

const { membership, out_of_network: outOfNetwork } = practice.insurance;

export function Savings() {
  return (
    <section aria-labelledby="savings-title" className="bg-secondary">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-16 sm:px-6">
        <h2 id="savings-title" className="text-3xl font-bold sm:text-4xl">
          Ways to pay less
        </h2>
        <div className="grid gap-10 md:grid-cols-3 md:gap-8">
          <div className="flex flex-col gap-3">
            <h3 className="text-xl font-semibold">
              Membership plan, ${membership.monthly_price_usd} a month
            </h3>
            <p className="text-muted-foreground">
              No insurance? The plan covers {membership.includes}.
            </p>
            <AskButton
              variant="link"
              className="self-start px-0"
              question="Tell me about the membership plan."
            >
              Ask about the membership plan
            </AskButton>
          </div>
          <div className="flex flex-col gap-3">
            <h3 className="text-xl font-semibold">Free Invisalign consultation</h3>
            <p className="text-muted-foreground">
              Find out if clear aligners are right for you before you commit to anything.
            </p>
            <AskButton
              variant="link"
              className="self-start px-0"
              question="I'd like to book a free Invisalign consultation."
            >
              Book a free consultation
            </AskButton>
          </div>
          <div className="flex flex-col gap-3">
            <h3 className="text-xl font-semibold">Out-of-network insurance</h3>
            <p className="text-muted-foreground">{outOfNetwork}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
