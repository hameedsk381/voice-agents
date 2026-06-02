"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HttpClient = exports.VoiseClient = void 0;
const resources_1 = require("./resources");
class VoiseClient {
    constructor(opts = {}) {
        const baseUrl = (opts.baseUrl || "http://localhost:8001").replace(/\/+$/, "");
        const apiKey = opts.apiKey || "";
        const timeout = opts.timeout || 30000;
        const http = new HttpClient(baseUrl, apiKey, timeout);
        this.agents = new resources_1.AgentsResource(http);
        this.campaigns = new resources_1.CampaignsResource(http);
        this.workflows = new resources_1.WorkflowsResource(http);
        this.telephony = new resources_1.TelephonyResource(http);
        this.knowledge = new resources_1.KnowledgeResource(http);
        this.voices = new resources_1.VoicesResource(http);
        this.phoneNumbers = new resources_1.PhoneNumbersResource(http);
    }
}
exports.VoiseClient = VoiseClient;
class HttpClient {
    constructor(baseUrl, apiKey, timeout) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.timeout = timeout;
    }
    async request(method, path, body, opts) {
        const url = `${this.baseUrl}/api/v1${path}`;
        const headers = {};
        if (this.apiKey) {
            headers["Authorization"] = `Bearer ${this.apiKey}`;
        }
        if (body && !opts?.formData) {
            headers["Content-Type"] = "application/json";
        }
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        try {
            const res = await fetch(url, {
                method,
                headers,
                body: body
                    ? opts?.formData
                        ? body
                        : JSON.stringify(body)
                    : undefined,
                signal: controller.signal,
            });
            if (!res.ok) {
                const errBody = await res.json().catch(() => ({}));
                const detail = errBody.detail || errBody.message || res.statusText;
                throw new Error(typeof detail === "string" ? detail : `${method} ${path} failed`);
            }
            return res;
        }
        finally {
            clearTimeout(timeoutId);
        }
    }
    async get(path) {
        const res = await this.request("GET", path);
        return res.json();
    }
    async post(path, data, opts) {
        const res = await this.request("POST", path, data, opts);
        return res.json();
    }
    async put(path, data) {
        const res = await this.request("PUT", path, data);
        return res.json();
    }
    async patch(path, data) {
        const res = await this.request("PATCH", path, data);
        return res.json();
    }
    async delete(path) {
        await this.request("DELETE", path);
    }
}
exports.HttpClient = HttpClient;
//# sourceMappingURL=client.js.map