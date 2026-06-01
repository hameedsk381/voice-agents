import type { VoiseClientOptions } from "./types";
import {
  AgentsResource,
  CampaignsResource,
  WorkflowsResource,
  TelephonyResource,
  KnowledgeResource,
  VoicesResource,
  PhoneNumbersResource,
} from "./resources";

export class VoiseClient {
  public readonly agents: AgentsResource;
  public readonly campaigns: CampaignsResource;
  public readonly workflows: WorkflowsResource;
  public readonly telephony: TelephonyResource;
  public readonly knowledge: KnowledgeResource;
  public readonly voices: VoicesResource;
  public readonly phoneNumbers: PhoneNumbersResource;

  constructor(opts: VoiseClientOptions = {}) {
    const baseUrl = (opts.baseUrl || "http://localhost:8001").replace(/\/+$/, "");
    const apiKey = opts.apiKey || "";
    const timeout = opts.timeout || 30000;

    const http = new HttpClient(baseUrl, apiKey, timeout);

    this.agents = new AgentsResource(http);
    this.campaigns = new CampaignsResource(http);
    this.workflows = new WorkflowsResource(http);
    this.telephony = new TelephonyResource(http);
    this.knowledge = new KnowledgeResource(http);
    this.voices = new VoicesResource(http);
    this.phoneNumbers = new PhoneNumbersResource(http);
  }
}

export class HttpClient {
  constructor(
    public readonly baseUrl: string,
    public readonly apiKey: string,
    public readonly timeout: number,
  ) {}

  private async request(
    method: string,
    path: string,
    body?: unknown,
    opts?: { formData?: boolean },
  ): Promise<Response> {
    const url = `${this.baseUrl}/api/v1${path}`;
    const headers: Record<string, string> = {};
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
            ? (body as FormData)
            : JSON.stringify(body)
          : undefined,
        signal: controller.signal,
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        const detail =
          errBody.detail || errBody.message || res.statusText;
        throw new Error(
          typeof detail === "string" ? detail : `${method} ${path} failed`,
        );
      }

      return res;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async get(path: string): Promise<unknown> {
    const res = await this.request("GET", path);
    return res.json();
  }

  async post(path: string, data?: unknown, opts?: { formData?: boolean }): Promise<unknown> {
    const res = await this.request("POST", path, data, opts);
    return res.json();
  }

  async put(path: string, data?: unknown): Promise<unknown> {
    const res = await this.request("PUT", path, data);
    return res.json();
  }

  async patch(path: string, data?: unknown): Promise<unknown> {
    const res = await this.request("PATCH", path, data);
    return res.json();
  }

  async delete(path: string): Promise<void> {
    await this.request("DELETE", path);
  }
}
