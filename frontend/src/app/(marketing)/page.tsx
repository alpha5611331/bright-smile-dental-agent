import { Emergencies } from "@/components/marketing/emergencies";
import { FirstVisit } from "@/components/marketing/first-visit";
import { Hero } from "@/components/marketing/hero";
import { Insurance } from "@/components/marketing/insurance";
import { Locations } from "@/components/marketing/locations";
import { PriceList } from "@/components/marketing/price-list";
import { Savings } from "@/components/marketing/savings";

export default function HomePage() {
  return (
    <>
      <Hero />
      <PriceList />
      <Savings />
      <Locations />
      <Insurance />
      <FirstVisit />
      <Emergencies />
    </>
  );
}
