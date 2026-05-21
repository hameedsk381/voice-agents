/**
 * User-facing copy for Voise AI — no vendor or infrastructure names in the product UI.
 */

export const PERSONALIZATION_FIELDS = [
  { key: "agentName", label: "Agent name", hint: "Your agent's display name" },
  { key: "companyName", label: "Company", hint: "Your organization" },
  { key: "customerName", label: "Customer name", hint: "Who you're speaking with" },
  { key: "language", label: "Language", hint: "Call language" },
  { key: "role", label: "Role", hint: "Agent role or title" },
  { key: "campaignName", label: "Campaign name", hint: "Outbound campaign" },
  { key: "contactName", label: "Contact name", hint: "Person being called" },
] as const;

export function personalizationToken(key: string): string {
  return `{{${key}}}`;
}
