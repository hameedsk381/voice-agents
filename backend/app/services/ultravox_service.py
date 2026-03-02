from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from app.core.config import settings


class UltravoxService:
    """Thin async client for Ultravox REST endpoints used by this project."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.api_key = api_key or settings.ULTRAVOX_API_KEY
        self.base_url = (base_url or settings.ULTRAVOX_BASE_URL).rstrip("/")
        self.timeout = timeout_seconds

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key or "",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        if path.startswith("/"):
            return f"{self.base_url}{path}"
        return f"{self.base_url}/{path}"

    async def create_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("Ultravox API key is not configured")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self._url("/calls"),
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def create_server_websocket_call(
        self,
        system_prompt: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        selected_tools: Optional[List[Dict[str, Any]]] = None,
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "systemPrompt": system_prompt,
            "model": model or settings.ULTRAVOX_MODEL,
            "voice": voice or settings.ULTRAVOX_VOICE,
            "medium": {
                "serverWebSocket": {
                    "inputSampleRate": settings.ULTRAVOX_INPUT_SAMPLE_RATE,
                    "outputSampleRate": settings.ULTRAVOX_OUTPUT_SAMPLE_RATE,
                    "clientBufferSizeMs": settings.ULTRAVOX_CLIENT_BUFFER_MS,
                    "dataMessages": {
                        "transcript": True,
                        "state": True,
                        "clientToolInvocation": True,
                        "playbackClearBuffer": True,
                    },
                }
            },
        }

        if metadata:
            payload["metadata"] = {
                str(key): str(value)
                for key, value in metadata.items()
                if value is not None
            }
        if selected_tools:
            payload["selectedTools"] = selected_tools
        if initial_state:
            payload["initialState"] = initial_state

        return await self.create_call(payload)

    async def list_voices(self) -> List[Dict[str, Any]]:
        """
        Returns normalized voice list for frontend compatibility.
        """
        if not self.enabled:
            return []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self._url("/voices"),
                headers={"X-API-Key": self.api_key or ""},
            )
            response.raise_for_status()
            data = response.json()

        if isinstance(data, dict):
            voices_raw = data.get("voices") or data.get("items") or []
        elif isinstance(data, list):
            voices_raw = data
        else:
            voices_raw = []

        normalized: List[Dict[str, Any]] = []
        for item in voices_raw:
            voice_id = item.get("voiceId") or item.get("id")
            if not voice_id:
                continue

            ownership = item.get("ownership", "public")
            normalized.append(
                {
                    "id": voice_id,
                    "name": item.get("name", str(voice_id)),
                    "type": "cloned" if ownership == "private" else "standard",
                    "provider": item.get("provider"),
                    "preview_url": item.get("previewUrl"),
                }
            )

        return normalized

    async def clone_voice(
        self,
        file_path: str,
        name: str,
        description: Optional[str] = None,
        language: str = "en-US",
    ) -> Optional[str]:
        """
        Create a cloned voice using Ultravox voice-cloning API.
        """
        if not self.enabled:
            return None

        form_data: Dict[str, Any] = {
            "name": name,
            "language": language,
        }
        if description:
            form_data["description"] = description

        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.split("/")[-1], f)}
                headers = {"X-API-Key": self.api_key or ""}
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self._url("/voices"),
                        data=form_data,
                        files=files,
                        headers=headers,
                    )
                    response.raise_for_status()
                    payload = response.json()
                    return payload.get("voiceId") or payload.get("id")
        except Exception as exc:
            logger.error(f"Ultravox voice cloning failed: {exc}")
            return None

    async def delete_voice(self, voice_id: str) -> bool:
        if not self.enabled:
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    self._url(f"/voices/{voice_id}"),
                    headers={"X-API-Key": self.api_key or ""},
                )
                if response.status_code in (200, 204):
                    return True
                logger.warning(
                    f"Ultravox delete voice returned {response.status_code}: {response.text}"
                )
                return False
        except Exception as exc:
            logger.error(f"Ultravox delete voice failed: {exc}")
            return False
