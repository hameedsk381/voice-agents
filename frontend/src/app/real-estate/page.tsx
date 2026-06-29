import VerticalPage from "@/components/VerticalPage";

export const metadata = { title: "Voise AI for Real Estate | Qualify Every Lead Before Your Team Picks Up" };

export default function RealEstatePage() {
  return (
    <VerticalPage
      industry="Real Estate"
      badge="🏠 Voise AI for Real Estate"
      headline={'Qualify Every Lead <span class="text-primary">Before Your Sales</span><br />Team Picks Up the Phone'}
      subheadline="Stop wasting site visits on unqualified prospects. Voise AI pre-screens every inbound lead — capturing budget, timeline, and location preference — so your closers only talk to buyers who are ready to act."
      stats={[
        { value: "5×", label: "More Qualified Leads" },
        { value: "0", label: "Leads Lost After Hours" },
        { value: "12", label: "Indian Languages" },
      ]}
      demoLabel="See the Real Estate Demo"
      useCases={[
        {
          title: "Inbound Lead Pre-Screening",
          description: "Every enquiry — web, portal, or referral — gets an immediate callback from a Voise AI agent that qualifies intent, budget, and preferred location before a human ever calls.",
          outcome: "Cut unqualified site visits by 70%",
        },
        {
          title: "Site Visit Scheduling",
          description: "Agent checks availability, proposes slots, and books a confirmed site visit directly into your calendar — with an SMS confirmation sent to the prospect.",
          outcome: "5× more site visits booked without sales team effort",
        },
        {
          title: "After-Hours Lead Capture",
          description: "Portals like MagicBricks and 99acres generate leads at all hours. Voise AI responds within seconds — day, night, and weekends — so no lead ever goes cold.",
          outcome: "Zero leads lost outside business hours",
        },
      ]}
      howItWorks={[
        {
          step: "01",
          title: "Connect your lead source",
          description: "Plug in your CRM, portal webhook, or landing page form. Voise AI fires an outbound call the moment a lead comes in.",
        },
        {
          step: "02",
          title: "Agent qualifies the lead",
          description: "A fluent AI agent asks the right questions in the buyer's language — intent, budget, location, timeline — and handles objections naturally.",
        },
        {
          step: "03",
          title: "Qualified lead lands in your CRM",
          description: "Full call transcript, lead score, and booked site visit appointment sync automatically to HubSpot, Salesforce, or any webhook.",
        },
      ]}
      ctaHeadline={'Stop Chasing Leads.<br /><span class="text-primary">Let AI Qualify Them.</span>'}
      ctaDescription="Deploy a real estate AI agent in under 5 minutes. Watch it pre-screen leads, book site visits, and hand off only the serious buyers to your sales team."
    />
  );
}
