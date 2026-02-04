const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api/v1";

function getAuthHeader(): Record<string, string> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export async function fetchAgents() {
    const res = await fetch(`${API_URL}/agents/`, {
        cache: "no-store",
        headers: {
            ...getAuthHeader()
        }
    });
    if (!res.ok) {
        throw new Error("Failed to fetch agents");
    }
    return res.json();
}

export async function createAgent(data: any) {
    const res = await fetch(`${API_URL}/agents/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...getAuthHeader()
        },
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        throw new Error("Failed to create agent");
    }
    return res.json();
}

export async function deleteAgent(id: string) {
    const res = await fetch(`${API_URL}/agents/${id}`, {
        method: 'DELETE',
        headers: {
            ...getAuthHeader()
        }
    });
    if (!res.ok) {
        throw new Error("Failed to delete agent");
    }
    return res.json();
}

// Generic API Client
const api = {
    async get(endpoint: string) {
        const res = await fetch(`${API_URL}${endpoint}`, {
            headers: { ...getAuthHeader() }
        });
        if (!res.ok) throw new Error(`GET ${endpoint} failed`);
        return res.json();
    },
    async post(endpoint: string, data: any) {
        const res = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(`POST ${endpoint} failed`);
        return res.json();
    },
    async delete(endpoint: string) {
        const res = await fetch(`${API_URL}${endpoint}`, {
            method: 'DELETE',
            headers: { ...getAuthHeader() }
        });
        if (!res.ok) throw new Error(`DELETE ${endpoint} failed`);
        return res.json();
    }
};

export default api;
