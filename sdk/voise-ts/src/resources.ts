import type { HttpClient } from "./client";
import type { Agent, Campaign, CampaignContact, PhoneNumber, Voice, Workflow, WorkflowInstance } from "./types";

export class AgentsResource {
  constructor(private http: HttpClient) {}

  async list(): Promise<Agent[]> {
    return (await this.http.get("/agents")) as Agent[];
  }

  async get(id: string): Promise<Agent> {
    return (await this.http.get(`/agents/${id}`)) as Agent;
  }

  async create(data: { name: string } & Record<string, unknown>): Promise<Agent> {
    return (await this.http.post("/agents", data)) as Agent;
  }

  async update(id: string, data: Record<string, unknown>): Promise<Agent> {
    return (await this.http.put(`/agents/${id}`, data)) as Agent;
  }

  async delete(id: string): Promise<void> {
    await this.http.delete(`/agents/${id}`);
  }

  async analytics(id: string): Promise<Record<string, unknown>> {
    return (await this.http.get(`/agents/${id}/analytics`)) as Record<string, unknown>;
  }
}

export class CampaignsResource {
  constructor(private http: HttpClient) {}

  async list(): Promise<Campaign[]> {
    return (await this.http.get("/campaigns")) as Campaign[];
  }

  async get(id: string): Promise<Campaign> {
    return (await this.http.get(`/campaigns/${id}`)) as Campaign;
  }

  async create(data: { name: string; agent_id: string } & Record<string, unknown>): Promise<Campaign> {
    return (await this.http.post("/campaigns", data)) as Campaign;
  }

  async update(id: string, data: Record<string, unknown>): Promise<Campaign> {
    return (await this.http.put(`/campaigns/${id}`, data)) as Campaign;
  }

  async delete(id: string): Promise<void> {
    await this.http.delete(`/campaigns/${id}`);
  }

  async start(id: string): Promise<Campaign> {
    return (await this.http.post(`/campaigns/${id}/start`)) as Campaign;
  }

  async pause(id: string): Promise<Campaign> {
    return (await this.http.post(`/campaigns/${id}/pause`)) as Campaign;
  }

  async addContacts(id: string, contacts: { phone_number: string; contact_name?: string }[]): Promise<{ count: number }> {
    return (await this.http.post(`/campaigns/${id}/contacts`, { contacts })) as { count: number };
  }
}

export class WorkflowsResource {
  constructor(private http: HttpClient) {}

  async list(): Promise<Workflow[]> {
    return (await this.http.get("/workflows")) as Workflow[];
  }

  async get(id: string): Promise<Workflow> {
    return (await this.http.get(`/workflows/${id}`)) as Workflow;
  }

  async create(data: { name: string; definition?: Record<string, unknown> } & Record<string, unknown>): Promise<Workflow> {
    return (await this.http.post("/workflows", data)) as Workflow;
  }

  async update(id: string, data: Record<string, unknown>): Promise<Workflow> {
    return (await this.http.put(`/workflows/${id}`, data)) as Workflow;
  }

  async delete(id: string): Promise<void> {
    await this.http.delete(`/workflows/${id}`);
  }

  async publish(id: string): Promise<Workflow> {
    return (await this.http.post(`/workflows/${id}/publish`)) as Workflow;
  }

  async trigger(id: string, context?: Record<string, unknown>): Promise<{ instance_id: string; status: string }> {
    return (await this.http.post(`/workflows/trigger/${id}`, context || {})) as { instance_id: string; status: string };
  }

  async listInstances(id: string): Promise<WorkflowInstance[]> {
    return (await this.http.get(`/workflows/${id}/instances`)) as WorkflowInstance[];
  }

  async createInstance(id: string, data?: { context?: Record<string, unknown>; agent_id?: string }): Promise<WorkflowInstance> {
    return (await this.http.post(`/workflows/${id}/instances`, data || {})) as WorkflowInstance;
  }

  async getInstance(instanceId: string): Promise<WorkflowInstance> {
    return (await this.http.get(`/workflows/instances/${instanceId}`)) as WorkflowInstance;
  }

  async listTemplates(): Promise<Record<string, unknown>[]> {
    return (await this.http.get("/workflows/templates")) as Record<string, unknown>[];
  }
}

export class TelephonyResource {
  constructor(private http: HttpClient) {}

  async call(data: { agent_id: string; to: string; from?: string }): Promise<Record<string, unknown>> {
    return (await this.http.post("/telephony/outgoing", data)) as Record<string, unknown>;
  }
}

export class KnowledgeResource {
  constructor(private http: HttpClient) {}

  async add(agentId: string, data: { text: string } & Record<string, unknown>): Promise<Record<string, unknown>> {
    return (await this.http.post(`/knowledge/${agentId}`, data)) as Record<string, unknown>;
  }

  async list(agentId: string): Promise<Record<string, unknown>[]> {
    return (await this.http.get(`/knowledge/${agentId}`)) as Record<string, unknown>[];
  }

  async delete(id: string): Promise<void> {
    await this.http.delete(`/knowledge/${id}`);
  }

  async query(agentId: string, query: string, topK?: number): Promise<Record<string, unknown>[]> {
    const params = new URLSearchParams({ q: query });
    if (topK) params.set("top_k", String(topK));
    return (await this.http.get(`/knowledge/${agentId}/query?${params}`)) as Record<string, unknown>[];
  }
}

export class VoicesResource {
  constructor(private http: HttpClient) {}

  async list(language?: string): Promise<Voice[]> {
    const params = language ? `?primaryLanguage=${language}` : "";
    return (await this.http.get(`/voices${params}`)) as Voice[];
  }

  async delete(id: string): Promise<void> {
    await this.http.delete(`/voices/${id}`);
  }
}

export class PhoneNumbersResource {
  constructor(private http: HttpClient) {}

  async searchAvailable(countryCode?: string, areaCode?: string): Promise<PhoneNumber[]> {
    const params = new URLSearchParams();
    if (countryCode) params.set("country_code", countryCode);
    if (areaCode) params.set("area_code", areaCode);
    const qs = params.toString();
    return (await this.http.get(`/phone-numbers/available${qs ? `?${qs}` : ""}`)) as PhoneNumber[];
  }

  async purchase(phoneNumber: string): Promise<PhoneNumber> {
    return (await this.http.post("/phone-numbers/purchase", { phone_number: phoneNumber })) as PhoneNumber;
  }

  async listOwned(): Promise<PhoneNumber[]> {
    return (await this.http.get("/phone-numbers")) as PhoneNumber[];
  }

  async release(id: string): Promise<void> {
    await this.http.delete(`/phone-numbers/${id}`);
  }
}
