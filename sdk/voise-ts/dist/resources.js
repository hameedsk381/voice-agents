"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PhoneNumbersResource = exports.VoicesResource = exports.KnowledgeResource = exports.TelephonyResource = exports.WorkflowsResource = exports.CampaignsResource = exports.AgentsResource = void 0;
class AgentsResource {
    constructor(http) {
        this.http = http;
    }
    async list() {
        return (await this.http.get("/agents"));
    }
    async get(id) {
        return (await this.http.get(`/agents/${id}`));
    }
    async create(data) {
        return (await this.http.post("/agents", data));
    }
    async update(id, data) {
        return (await this.http.put(`/agents/${id}`, data));
    }
    async delete(id) {
        await this.http.delete(`/agents/${id}`);
    }
    async analytics(id) {
        return (await this.http.get(`/agents/${id}/analytics`));
    }
}
exports.AgentsResource = AgentsResource;
class CampaignsResource {
    constructor(http) {
        this.http = http;
    }
    async list() {
        return (await this.http.get("/campaigns"));
    }
    async get(id) {
        return (await this.http.get(`/campaigns/${id}`));
    }
    async create(data) {
        return (await this.http.post("/campaigns", data));
    }
    async update(id, data) {
        return (await this.http.put(`/campaigns/${id}`, data));
    }
    async delete(id) {
        await this.http.delete(`/campaigns/${id}`);
    }
    async start(id) {
        return (await this.http.post(`/campaigns/${id}/start`));
    }
    async pause(id) {
        return (await this.http.post(`/campaigns/${id}/pause`));
    }
    async addContacts(id, contacts) {
        return (await this.http.post(`/campaigns/${id}/contacts`, { contacts }));
    }
}
exports.CampaignsResource = CampaignsResource;
class WorkflowsResource {
    constructor(http) {
        this.http = http;
    }
    async list() {
        return (await this.http.get("/workflows"));
    }
    async get(id) {
        return (await this.http.get(`/workflows/${id}`));
    }
    async create(data) {
        return (await this.http.post("/workflows", data));
    }
    async update(id, data) {
        return (await this.http.put(`/workflows/${id}`, data));
    }
    async delete(id) {
        await this.http.delete(`/workflows/${id}`);
    }
    async publish(id) {
        return (await this.http.post(`/workflows/${id}/publish`));
    }
    async trigger(id, context) {
        return (await this.http.post(`/workflows/trigger/${id}`, context || {}));
    }
    async listInstances(id) {
        return (await this.http.get(`/workflows/${id}/instances`));
    }
    async createInstance(id, data) {
        return (await this.http.post(`/workflows/${id}/instances`, data || {}));
    }
    async getInstance(instanceId) {
        return (await this.http.get(`/workflows/instances/${instanceId}`));
    }
    async listTemplates() {
        return (await this.http.get("/workflows/templates"));
    }
}
exports.WorkflowsResource = WorkflowsResource;
class TelephonyResource {
    constructor(http) {
        this.http = http;
    }
    async call(data) {
        return (await this.http.post("/telephony/outgoing", data));
    }
}
exports.TelephonyResource = TelephonyResource;
class KnowledgeResource {
    constructor(http) {
        this.http = http;
    }
    async add(agentId, data) {
        return (await this.http.post(`/knowledge/${agentId}`, data));
    }
    async list(agentId) {
        return (await this.http.get(`/knowledge/${agentId}`));
    }
    async delete(id) {
        await this.http.delete(`/knowledge/${id}`);
    }
    async query(agentId, query, topK) {
        const params = new URLSearchParams({ q: query });
        if (topK)
            params.set("top_k", String(topK));
        return (await this.http.get(`/knowledge/${agentId}/query?${params}`));
    }
}
exports.KnowledgeResource = KnowledgeResource;
class VoicesResource {
    constructor(http) {
        this.http = http;
    }
    async list(language) {
        const params = language ? `?primaryLanguage=${language}` : "";
        return (await this.http.get(`/voices${params}`));
    }
    async delete(id) {
        await this.http.delete(`/voices/${id}`);
    }
}
exports.VoicesResource = VoicesResource;
class PhoneNumbersResource {
    constructor(http) {
        this.http = http;
    }
    async searchAvailable(countryCode, areaCode) {
        const params = new URLSearchParams();
        if (countryCode)
            params.set("country_code", countryCode);
        if (areaCode)
            params.set("area_code", areaCode);
        const qs = params.toString();
        return (await this.http.get(`/phone-numbers/available${qs ? `?${qs}` : ""}`));
    }
    async purchase(phoneNumber) {
        return (await this.http.post("/phone-numbers/purchase", { phone_number: phoneNumber }));
    }
    async listOwned() {
        return (await this.http.get("/phone-numbers"));
    }
    async release(id) {
        await this.http.delete(`/phone-numbers/${id}`);
    }
}
exports.PhoneNumbersResource = PhoneNumbersResource;
//# sourceMappingURL=resources.js.map