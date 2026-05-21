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
        if (!res.ok) throw new Error(`POST ${endpoint} (FormData) failed`);
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

export default api;
