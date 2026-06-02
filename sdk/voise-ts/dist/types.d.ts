export interface VoiseClientOptions {
    baseUrl?: string;
    apiKey?: string;
    timeout?: number;
}
export interface Agent {
    id: string;
    name: string;
    language?: string;
    voice?: string;
    is_active?: boolean;
    persona?: string;
    tools?: string[];
    goals?: Record<string, unknown>;
    config?: Record<string, unknown>;
    created_at?: string;
    updated_at?: string;
}
export interface Campaign {
    id: string;
    name: string;
    agent_id: string;
    workflow_id?: string;
    status: string;
    total_contacts: number;
    completed_calls: number;
    failed_calls: number;
    created_at?: string;
}
export interface CampaignContact {
    id: string;
    campaign_id: string;
    phone_number: string;
    contact_name?: string;
    status: string;
    custom_data?: Record<string, unknown>;
}
export interface Workflow {
    id: string;
    name: string;
    description?: string;
    category?: string;
    status: string;
    definition?: Record<string, unknown>;
    created_at?: string;
}
export interface WorkflowInstance {
    id: string;
    workflow_id: string;
    status: string;
    current_node_id?: string;
    context?: Record<string, unknown>;
    created_at?: string;
}
export interface PhoneNumber {
    id: string;
    phone_number: string;
    friendly_name?: string;
    capability?: string;
    is_active?: boolean;
}
export interface Voice {
    id: string;
    name: string;
    provider: string;
    language?: string;
    gender?: string;
}
