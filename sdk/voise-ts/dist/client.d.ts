import type { VoiseClientOptions } from "./types";
import { AgentsResource, CampaignsResource, WorkflowsResource, TelephonyResource, KnowledgeResource, VoicesResource, PhoneNumbersResource } from "./resources";
export declare class VoiseClient {
    readonly agents: AgentsResource;
    readonly campaigns: CampaignsResource;
    readonly workflows: WorkflowsResource;
    readonly telephony: TelephonyResource;
    readonly knowledge: KnowledgeResource;
    readonly voices: VoicesResource;
    readonly phoneNumbers: PhoneNumbersResource;
    constructor(opts?: VoiseClientOptions);
}
export declare class HttpClient {
    readonly baseUrl: string;
    readonly apiKey: string;
    readonly timeout: number;
    constructor(baseUrl: string, apiKey: string, timeout: number);
    private request;
    get(path: string): Promise<unknown>;
    post(path: string, data?: unknown, opts?: {
        formData?: boolean;
    }): Promise<unknown>;
    put(path: string, data?: unknown): Promise<unknown>;
    patch(path: string, data?: unknown): Promise<unknown>;
    delete(path: string): Promise<void>;
}
