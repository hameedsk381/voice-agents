import { getApiBaseUrl } from "./api-url";

export async function fetchAgents() {
    const res = await fetch(`${getApiBaseUrl()}/agents/`, {
        cache: "no-store",
        credentials: "include",
    });
    if (!res.ok) {
        throw new Error("Failed to fetch agents");
    }
    return res.json();
}

export async function createAgent(data: any) {
    const res = await fetch(`${getApiBaseUrl()}/agents/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: "include",
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        throw new Error("Failed to create agent");
    }
    return res.json();
}

export async function deleteAgent(id: string) {
    const res = await fetch(`${getApiBaseUrl()}/agents/${id}`, {
        method: 'DELETE',
        credentials: "include",
    });
    if (!res.ok) {
        throw new Error("Failed to delete agent");
    }
    return res.json();
}

// Generic API Client
const api = {
    async get(endpoint: string) {
        const res = await fetch(`${getApiBaseUrl()}${endpoint}`, {
            credentials: "include",
        });
        if (!res.ok) throw new Error(`GET ${endpoint} failed`);
        return res.json();
    },
    async post(endpoint: string, data: any) {
        const res = await fetch(`${getApiBaseUrl()}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: "include",
            body: JSON.stringify(data),
        });
        if (!res.ok) {
            const errBody = await res.json().catch(() => ({}));
            const detail = errBody.detail || errBody.message || res.statusText;
            throw new Error(typeof detail === "string" ? detail : `POST ${endpoint} failed`);
        }
        return res.json();
    },
    async postFormData(endpoint: string, formData: FormData) {
        const res = await fetch(`${getApiBaseUrl()}${endpoint}`, {
            method: 'POST',
            credentials: "include",
            body: formData,
        });
        if (!res.ok) {
            const errBody = await res.json().catch(() => ({}));
            const detail = errBody.detail || res.statusText;
            throw new Error(typeof detail === "string" ? detail : `POST ${endpoint} (FormData) failed`);
        }
        return res.json();
    },
    async put(endpoint: string, data: any) {
        const res = await fetch(`${getApiBaseUrl()}${endpoint}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: "include",
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(`PUT ${endpoint} failed`);
        return res.json();
    },
    async delete(endpoint: string) {
        const res = await fetch(`${getApiBaseUrl()}${endpoint}`, {
            method: 'DELETE',
            credentials: "include",
        });
        if (!res.ok) throw new Error(`DELETE ${endpoint} failed`);
        return res.json();
    }
};

// --- Policy API ---
export async function fetchPolicyRules() {
    return api.get("/policy/rules");
}

export async function createPolicyRule(data: any) {
    return api.post("/policy/rules", data);
}

export async function updatePolicyRule(id: string, data: any) {
    return api.put(`/policy/rules/${id}`, data);
}

export async function deletePolicyRule(id: string) {
    return api.delete(`/policy/rules/${id}`);
}

// --- Billing / Usage API ---
export async function fetchBillingUsage() {
    return api.get("/billing/usage");
}

export async function fetchBillingSubscription() {
    return api.get("/billing/subscription");
}

export async function fetchRateCard() {
    return api.get("/billing/rate-card");
}

export async function estimateCallCost(params: {
    duration_minutes?: number;
    stt_seconds?: number;
    tts_seconds?: number;
    llm_tokens?: number;
}) {
    const qs = new URLSearchParams();
    if (params.duration_minutes) qs.set("duration_minutes", String(params.duration_minutes));
    if (params.stt_seconds) qs.set("stt_seconds", String(params.stt_seconds));
    if (params.tts_seconds) qs.set("tts_seconds", String(params.tts_seconds));
    if (params.llm_tokens) qs.set("llm_tokens", String(params.llm_tokens));
    return api.get(`/billing/cost/estimate?${qs.toString()}`);
}

export async function fetchUsageRecords(metric?: string) {
    const qs = metric ? `?metric=${encodeURIComponent(metric)}` : "";
    return api.get(`/billing/usage/records${qs}`);
}

// --- Organization API ---
export async function fetchMyOrganization() {
    return api.get("/organizations/me");
}

export async function updateMyOrganization(data: { name?: string; settings?: Record<string, any> }) {
    return api.put("/organizations/me", data);
}

export async function fetchOrgMembers() {
    return api.get("/organizations/me/members");
}

export async function updateMemberRole(userId: string, role: string) {
    return api.put(`/organizations/me/members/${userId}/role`, { role });
}

export async function completeOnboarding() {
    return api.post("/organizations/me/onboarding/complete", {});
}

// --- Phone Number API ---
export async function searchAvailableNumbers(params: { country_code?: string; area_code?: string; contains?: string; limit?: number }) {
    const qs = new URLSearchParams();
    if (params.country_code) qs.set("country_code", params.country_code);
    if (params.area_code) qs.set("area_code", params.area_code);
    if (params.contains) qs.set("contains", params.contains);
    if (params.limit) qs.set("limit", String(params.limit));
    return api.get(`/phone-numbers/available?${qs.toString()}`);
}

export async function purchasePhoneNumber(data: { phone_number: string; friendly_name?: string; voice_url?: string }) {
    return api.post("/phone-numbers/purchase", data);
}

export async function fetchOwnedNumbers() {
    return api.get("/phone-numbers/owned");
}

export async function configurePhoneNumber(numberId: string, voiceUrl: string) {
    return api.post(`/phone-numbers/${numberId}/configure`, { voice_url: voiceUrl });
}

export async function releasePhoneNumber(numberId: string) {
    return api.delete(`/phone-numbers/${numberId}`);
}

export async function syncPhoneNumbers() {
    return api.post("/phone-numbers/sync", {});
}

export default api;
