import type { HttpClient } from "./client";
import type { Agent, Campaign, PhoneNumber, Voice, Workflow, WorkflowInstance } from "./types";
export declare class AgentsResource {
    private http;
    constructor(http: HttpClient);
    list(): Promise<Agent[]>;
    get(id: string): Promise<Agent>;
    create(data: {
        name: string;
    } & Record<string, unknown>): Promise<Agent>;
    update(id: string, data: Record<string, unknown>): Promise<Agent>;
    delete(id: string): Promise<void>;
    analytics(id: string): Promise<Record<string, unknown>>;
}
export declare class CampaignsResource {
    private http;
    constructor(http: HttpClient);
    list(): Promise<Campaign[]>;
    get(id: string): Promise<Campaign>;
    create(data: {
        name: string;
        agent_id: string;
    } & Record<string, unknown>): Promise<Campaign>;
    update(id: string, data: Record<string, unknown>): Promise<Campaign>;
    delete(id: string): Promise<void>;
    start(id: string): Promise<Campaign>;
    pause(id: string): Promise<Campaign>;
    addContacts(id: string, contacts: {
        phone_number: string;
        contact_name?: string;
    }[]): Promise<{
        count: number;
    }>;
}
export declare class WorkflowsResource {
    private http;
    constructor(http: HttpClient);
    list(): Promise<Workflow[]>;
    get(id: string): Promise<Workflow>;
    create(data: {
        name: string;
        definition?: Record<string, unknown>;
    } & Record<string, unknown>): Promise<Workflow>;
    update(id: string, data: Record<string, unknown>): Promise<Workflow>;
    delete(id: string): Promise<void>;
    publish(id: string): Promise<Workflow>;
    trigger(id: string, context?: Record<string, unknown>): Promise<{
        instance_id: string;
        status: string;
    }>;
    listInstances(id: string): Promise<WorkflowInstance[]>;
    createInstance(id: string, data?: {
        context?: Record<string, unknown>;
        agent_id?: string;
    }): Promise<WorkflowInstance>;
    getInstance(instanceId: string): Promise<WorkflowInstance>;
    listTemplates(): Promise<Record<string, unknown>[]>;
}
export declare class TelephonyResource {
    private http;
    constructor(http: HttpClient);
    call(data: {
        agent_id: string;
        to: string;
        from?: string;
    }): Promise<Record<string, unknown>>;
}
export declare class KnowledgeResource {
    private http;
    constructor(http: HttpClient);
    add(agentId: string, data: {
        text: string;
    } & Record<string, unknown>): Promise<Record<string, unknown>>;
    list(agentId: string): Promise<Record<string, unknown>[]>;
    delete(id: string): Promise<void>;
    query(agentId: string, query: string, topK?: number): Promise<Record<string, unknown>[]>;
}
export declare class VoicesResource {
    private http;
    constructor(http: HttpClient);
    list(language?: string): Promise<Voice[]>;
    delete(id: string): Promise<void>;
}
export declare class PhoneNumbersResource {
    private http;
    constructor(http: HttpClient);
    searchAvailable(countryCode?: string, areaCode?: string): Promise<PhoneNumber[]>;
    purchase(phoneNumber: string): Promise<PhoneNumber>;
    listOwned(): Promise<PhoneNumber[]>;
    release(id: string): Promise<void>;
}
