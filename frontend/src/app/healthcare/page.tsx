import VerticalPage from "@/components/VerticalPage";

export const metadata = { title: "Voise AI for Healthcare | Cut No-Shows by 60%" };

export default function HealthcarePage() {
  return (
    <VerticalPage
      industry="Healthcare"
      badge="🏥 Voise AI for Healthcare"
      headline={'Cut No-Shows by 60% —<br /><span class="text-primary">AI Handles Every</span><br />Appointment Reminder'}
      subheadline="Missed appointments cost clinics lakhs every month. Voise AI calls patients in Tamil, Kannada, Hindi, or English — confirming, rescheduling, or cancelling — so your front desk focuses on patients who walk in, not those who don't."
      stats={[
        { value: "60%", label: "Reduction in No-Shows" },
        { value: "24/7", label: "Patient Availability" },
        { value: "DPDP", label: "Act 2023 Compliant" },
      ]}
      demoLabel="See the Healthcare Demo"
      useCases={[
        {
          title: "Appointment Reminders",
          description: "Automated calls 24 hours and 1 hour before each appointment. Patient confirms with a keypress or asks to reschedule — all logged instantly.",
          outcome: "60% fewer no-shows within the first month",
        },
        {
          title: "Inbound Booking",
          description: "Patients call in to book appointments and get routed directly to an AI agent that checks availability and confirms a slot — in their language.",
          outcome: "Zero hold times, 24/7 availability for new bookings",
        },
        {
          title: "Post-Visit Follow-Up",
          description: "A follow-up call checks on patient recovery, prompts medication adherence, and schedules the next visit — improving outcomes and retention.",
          outcome: "Higher patient satisfaction and repeat visit rates",
        },
      ]}
      howItWorks={[
        {
          step: "01",
          title: "Sync your appointment system",
          description: "Connect your HMS or Google Calendar via webhook. Voise AI reads upcoming appointments and schedules reminder calls automatically.",
        },
        {
          step: "02",
          title: "Patients confirm or reschedule",
          description: "A natural-sounding call in the patient's language confirms attendance, books a new slot if needed, and sends an SMS summary.",
        },
        {
          step: "03",
          title: "Front desk sees real-time updates",
          description: "Confirmed, rescheduled, and cancelled appointments sync back to your HMS. No manual entry, no phone tag.",
        },
      ]}
      ctaHeadline={'Every Empty Slot<br />Costs <span class="text-primary">Real Money.</span>'}
      ctaDescription="Deploy a healthcare AI agent in minutes. It speaks Tamil, Kannada, Hindi, and 9 more Indian languages — and it works around the clock so your staff doesn't have to."
    />
  );
}
