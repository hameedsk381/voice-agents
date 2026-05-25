export type UserRole = 'admin' | 'manager' | 'agent' | 'viewer';

export interface User {
    id: string;
    email: string;
    full_name: string | null;
    role: UserRole;
    is_active: boolean;
    created_at: string;
}

export interface Agent {
    id: string;
    name: string;
    description: string | null;
    system_prompt: string | null;
    voice_id: string | null;
    llm_config: Record<string, any> | null;
    goals: string | null;
    success_criteria: string[] | null;
    failure_conditions: string[] | null;
    is_active: boolean;
    created_at: string;
}

export interface CallLog {
    id: string;
    session_id: string;
    agent_id: string;
    agent_name?: string;
    caller_id: string | null;
    campaign_id: string | null;
    start_time: string;
    end_time: string;
    duration_seconds: number;
    avg_latency_ms: number;
    ttfap_ms: number;
    total_turns: number;
    total_tokens: number;
    estimated_cost: number;
    status: string;
    end_reason: string;
    outcome: 'SUCCESS' | 'FAILURE' | 'NEUTRAL';
    outcome_reason: string | null;
    transcript: Array<{ role: string; content: string; timestamp?: string }>;
    signature: string;
}

export interface AuditLog {
    id: string;
    session_id: string;
    timestamp: string;
    user_input: string;
    agent_response: string;
    is_compliant: boolean;
    violations: string[];
    risk_score: number;
}

export interface Campaign {
    id: string;
    name: string;
    description: string | null;
    agent_id: string;
    status: string;
    created_at: string;
    total_contacts?: number;
    completed_calls?: number;
    failed_calls?: number;
}

export interface PendingAction {
    id: string;
    session_id: string;
    action_type: string;
    description: string;
    payload: Record<string, any>;
    status: string;
    created_at: string;
    agent_id: string;
}

export interface PolicyRule {
    id: string;
    organization_id?: string;
    name: string;
    description: string;
    tool_name: string;
    conditions: Record<string, any>;
    action: 'permit' | 'deny' | 'escalate';
    priority: number;
    enabled: boolean;
    created_at: string;
    updated_at: string;
}

// --- Billing Types ---
export interface SubscriptionInfo {
    id?: string;
    plan: string;
    status: string;
    billing_period_start: string;
    billing_period_end: string | null;
    auto_renew?: string;
    trial?: {
        starts_at: string | null;
        ends_at: string | null;
    } | null;
    created_at?: string;
}

export interface UsageSummary {
    plan: string;
    usage: Record<string, number>;
    limits: Record<string, number>;
    percentages: Record<string, number>;
    trial?: {
        active: boolean;
        starts_at?: string | null;
        ends_at?: string | null;
        days_remaining?: number;
        expired?: boolean;
    };
}

export interface RateCardInfo {
    plan: string;
    rates: Record<string, {
        unit: string;
        price_per_unit: number;
        included_units: number;
        overage_price_per_unit: number | null;
    }>;
}

export interface CostEstimate {
    plan: string;
    estimated_cost: number;
}

export interface UsageRecordItem {
    id: string;
    metric: string;
    quantity: number;
    unit: string;
    session_id: string | null;
    recorded_at: string;
}

// --- Phone Number Types ---
export interface PhoneNumberInfo {
    id: string;
    phone_number: string;
    friendly_name: string | null;
    twilio_sid: string;
    capabilities: { voice: boolean; sms: boolean; mms: boolean };
    region: string | null;
    is_active: boolean;
    created_at: string;
}

export interface AvailablePhoneNumber {
    phone_number: string;
    friendly_name: string;
    locality: string | null;
    region: string | null;
    capabilities: { voice: boolean; sms: boolean; mms: boolean };
    price: string | null;
}

// --- Organization Types ---
export interface OrganizationInfo {
    id: string;
    name: string;
    domain: string | null;
    subscription_plan: string;
    is_active: boolean;
    settings: Record<string, any>;
    created_at: string;
    updated_at: string;
}

export interface OrgMember {
    id: string;
    email: string;
    full_name: string | null;
    role: string;
    is_active: boolean;
    is_superuser: boolean;
    created_at: string;
    last_login: string | null;
}

export interface OrgUpdatePayload {
    name?: string;
    settings?: Record<string, any>;
}
