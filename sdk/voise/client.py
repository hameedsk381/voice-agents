from typing import Any, Dict, List, Optional

import httpx


class VoiseClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        headers: Dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._http = httpx.Client(base_url=self.base_url, headers=headers, timeout=timeout)
        self.agents = _AgentsResource(self._http)
        self.campaigns = _CampaignsResource(self._http)
        self.telephony = _TelephonyResource(self._http)
        self.workflows = _WorkflowsResource(self._http)
        self.knowledge = _KnowledgeResource(self._http)
        self.voices = _VoicesResource(self._http)
        self.phone_numbers = _PhoneNumbersResource(self._http)

    def close(self) -> None:
        self._http.close()


class _AgentsResource:
    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def list(self) -> List[Dict[str, Any]]:
        r = self._http.get("/api/v1/agents")
        r.raise_for_status()
        return r.json()

    def get(self, agent_id: str) -> Dict[str, Any]:
        r = self._http.get(f"/api/v1/agents/{agent_id}")
        r.raise_for_status()
        return r.json()

    def create(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"name": name, **kwargs}
        r = self._http.post("/api/v1/agents", json=payload)
        r.raise_for_status()
        return r.json()

    def update(self, agent_id: str, **kwargs: Any) -> Dict[str, Any]:
        r = self._http.patch(f"/api/v1/agents/{agent_id}", json=kwargs)
        r.raise_for_status()
        return r.json()

    def delete(self, agent_id: str) -> None:
        r = self._http.delete(f"/api/v1/agents/{agent_id}")
        r.raise_for_status()


class _CampaignsResource:
    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def list(self) -> List[Dict[str, Any]]:
        r = self._http.get("/api/v1/campaigns")
        r.raise_for_status()
        return r.json()

    def get(self, campaign_id: str) -> Dict[str, Any]:
        r = self._http.get(f"/api/v1/campaigns/{campaign_id}")
        r.raise_for_status()
        return r.json()

    def create(self, name: str, agent_id: str, **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"name": name, "agent_id": agent_id, **kwargs}
        r = self._http.post("/api/v1/campaigns", json=payload)
        r.raise_for_status()
        return r.json()

    def start(self, campaign_id: str) -> Dict[str, Any]:
        r = self._http.post(f"/api/v1/campaigns/{campaign_id}/start")
        r.raise_for_status()
        return r.json()

    def pause(self, campaign_id: str) -> Dict[str, Any]:
        r = self._http.post(f"/api/v1/campaigns/{campaign_id}/pause")
        r.raise_for_status()
        return r.json()

    def add_contacts(self, campaign_id: str, contacts: List[Dict[str, Any]]) -> int:
        r = self._http.post(f"/api/v1/campaigns/{campaign_id}/contacts", json={"contacts": contacts})
        r.raise_for_status()
        return r.json().get("count", 0)


class _TelephonyResource:
    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def call(self, agent_id: str, to: str, from_: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"agent_id": agent_id, "to": to}
        if from_:
            payload["from"] = from_
        r = self._http.post("/api/v1/telephony/outgoing", json=payload)
        r.raise_for_status()
        return r.json()


class _WorkflowsResource:
    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def list(self) -> List[Dict[str, Any]]:
        r = self._http.get("/api/v1/workflows")
        r.raise_for_status()
        return r.json()

    def get(self, workflow_id: str) -> Dict[str, Any]:
        r = self._http.get(f"/api/v1/workflows/{workflow_id}")
        r.raise_for_status()
        return r.json()

    def create(self, name: str, definition: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"name": name, "definition": definition, **kwargs}
        r = self._http.post("/api/v1/workflows", json=payload)
        r.raise_for_status()
        return r.json()


class _KnowledgeResource:
    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def add(self, agent_id: str, text: str, **kwargs: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"agent_id": agent_id, "text": text, **kwargs}
        r = self._http.post("/api/v1/knowledge", json=payload)
        r.raise_for_status()
        return r.json()

    def query(self, agent_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        r = self._http.get(f"/api/v1/knowledge/query", params={"agent_id": agent_id, "query": query, "top_k": top_k})
        r.raise_for_status()
        return r.json()


class _VoicesResource:
    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def list(self) -> List[Dict[str, Any]]:
        r = self._http.get("/api/v1/voices")
        r.raise_for_status()
        return r.json()


class _PhoneNumbersResource:
    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def list_available(self, area_code: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if area_code:
            params["area_code"] = area_code
        r = self._http.get("/api/v1/phone-numbers/available", params=params)
        r.raise_for_status()
        return r.json()

    def purchase(self, phone_number: str) -> Dict[str, Any]:
        r = self._http.post("/api/v1/phone-numbers/purchase", json={"phone_number": phone_number})
        r.raise_for_status()
        return r.json()

    def list_owned(self) -> List[Dict[str, Any]]:
        r = self._http.get("/api/v1/phone-numbers")
        r.raise_for_status()
        return r.json()
