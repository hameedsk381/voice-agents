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
