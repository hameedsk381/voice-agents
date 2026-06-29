import VerticalPage from "@/components/VerticalPage";

export const metadata = { title: "Voise AI for Collections | Recover 3× More EMIs" };

export default function CollectionsPage() {
  return (
    <VerticalPage
      industry="Collections"
      badge="💰 Voise AI for Collections & NBFCs"
      headline={'Recover 3× More EMIs<br /><span class="text-primary">Without Adding</span><br />a Single Collector'}
      subheadline="Manual calling teams are expensive, inconsistent, and can't scale. Voise AI handles thousands of simultaneous collection calls — empathetically negotiating EMI splits, extension deadlines, and payment promises — while staying fully DPDP compliant."
      stats={[
        { value: "3×", label: "Payment Recovery Rate" },
        { value: "47%", label: "Promise-to-Pay Rate" },
        { value: "₹0", label: "Cost Per Call" },
      ]}
      demoLabel="See the Collections Demo"
      useCases={[
        {
          title: "EMI Payment Reminders",
          description: "Automated outbound calls in Hindi, Tamil, or Telugu remind borrowers of upcoming EMIs — before they miss the due date, reducing delinquency at the source.",
          outcome: "3× recovery rate vs. manual calling teams",
        },
        {
          title: "Empathetic Negotiation",
          description: "When borrowers push back, the agent doesn't hang up. It offers EMI splits, extends deadlines, and proposes payment plans — all within your configured policy limits.",
          outcome: "Promise-to-pay rate up from 18% to 47%",
        },
        {
          title: "CRM & Audit Logging",
          description: "Every call outcome — confirmed payment, negotiated date, or no-contact — is logged directly to your CRM with a signed transcript for compliance audits.",
          outcome: "Full DPDP Act 2023 audit trail on every interaction",
        },
      ]}
      howItWorks={[
        {
          step: "01",
          title: "Upload your contact list",
          description: "Import overdue accounts via CSV or CRM sync. Set your negotiation parameters — max extension days, minimum payment thresholds, number of retry attempts.",
        },
        {
          step: "02",
          title: "Agents run the campaign",
          description: "Voise AI calls thousands of borrowers simultaneously in their language, handles objections, and logs every promise to pay with a timestamp.",
        },
        {
          step: "03",
          title: "Review outcomes in the dashboard",
          description: "See real-time recovery rates, promise-to-pay counts, and failed contacts. Re-trigger follow-up calls for missed promises automatically.",
        },
      ]}
      ctaHeadline={'Pay Only When We<br /><span class="text-primary">Recover Your Money.</span>'}
      ctaDescription="Start with a free 30-day pilot on your own overdue accounts. After that, you pay per promise-to-pay captured and per recovered EMI — never per minute, never a retainer. The agent works 24/7, in your borrowers' language, fully DPDP & RBI compliant."
    />
  );
}
