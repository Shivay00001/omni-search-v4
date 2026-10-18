"""
SentinelProvider — industry-grade LLM orchestrator with automatic failover.

Provider chain (free/no-key first, then key-based):
  1. pollinations  — keyless POST       (https://text.pollinations.ai)
  2. g4f-gpt4      — keyless via g4f package
  3. g4f-gpt35     — keyless via g4f package
  4. puter         — needs PUTER_API_TOKEN (https://api.puter.com/puterai/openai/v1/)
  5. groq          — needs GROQ_API_KEY (https://api.groq.com/openai/v1/)
  6. openrouter    — needs OPENROUTER_API_KEY (https://openrouter.ai/api/v1/)
  7. llm7          — needs LLM7_API_KEY (https://api.llm7.io/v1/)
  8. gemini        — needs GEMINI_API_KEY (google-generativeai SDK)

Each successful response is tagged with its provider id so the frontend
can display it. Streaming yields a `__PROVIDER__:<id>` marker first,
matching the existing __SOURCES__/__THOUGHT__ marker protocol.

Env vars (all optional except as noted):
  PUTER_API_TOKEN, PUTER_MODEL (default: gpt-5.4-nano)
  GROQ_API_KEY, GROQ_MODEL (default: llama-3.3-70b-versatile)
  OPENROUTER_API_KEY, OPENROUTER_MODEL (default: meta-llama/llama-3.3-70b-instruct:free)
  GEMINI_API_KEY
  LLM7_API_KEY, LLM7_MODEL (default: gemini-3.1-flash-lite)
  POLLINATIONS_MODEL (default: openai)
"""
import os
import json
import asyncio
from typing import AsyncGenerator, Optional, List, Dict

import httpx

try:
    import g4f
    _HAS_G4F = True
except ImportError:
    _HAS_G4F = False

try:
    import google.generativeai as genai
    _HAS_GENAI = True
except ImportError:
    _HAS_GENAI = False

# ---------------------------------------------------------------------------
# Provider registry — single source of truth for /providers endpoint + UI
# ---------------------------------------------------------------------------
PROVIDERS: List[Dict] = [
    {"id": "pollinations", "label": "Pollinations", "note": "Free, no key",
     "needs_key": False, "env_key": None},
    {"id": "g4f-gpt4", "label": "GPT-4 (g4f)", "note": "Free, no key",
     "needs_key": False, "env_key": None},
    {"id": "g4f-gpt35", "label": "GPT-3.5 (g4f)", "note": "Free, no key",
     "needs_key": False, "env_key": None},
    {"id": "puter", "label": "Puter", "note": "Needs PUTER_API_TOKEN",
     "needs_key": True, "env_key": "PUTER_API_TOKEN"},
    {"id": "groq", "label": "Groq", "note": "Needs GROQ_API_KEY (free tier)",
     "needs_key": True, "env_key": "GROQ_API_KEY"},
    {"id": "openrouter", "label": "OpenRouter", "note": "Needs OPENROUTER_API_KEY",
     "needs_key": True, "env_key": "OPENROUTER_API_KEY"},
    {"id": "llm7", "label": "LLM7", "note": "Needs LLM7_API_KEY (free at dash.llm7.io)",
     "needs_key": True, "env_key": "LLM7_API_KEY"},
    {"id": "gemini", "label": "Gemini", "note": "Needs GEMINI_API_KEY (free tier)",
     "needs_key": True, "env_key": "GEMINI_API_KEY"},
]


async def _stream_openai_compatible(url: str, headers: Dict, payload: Dict):
    """Yield text chunks from an OpenAI-compatible SSE stream."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    delta = obj["choices"][0]["delta"]
                    content = delta.get("content")
                    if content:
                        yield content
                except (KeyError, IndexError, ValueError):
                    continue


async def _post_openai_compatible(url: str, headers: Dict, payload: Dict) -> str:
    """Non-streaming OpenAI-compatible chat completion. Returns full text."""
    payload = {**payload, "stream": False}
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        obj = resp.json()
        return obj["choices"][0]["message"]["content"]


class SentinelProvider:
    """
    Industry-grade LLM orchestrator with automatic failover.
    Ensures 'Omni' never goes down.
    """

    def __init__(self):
        self.puter_token = os.getenv("PUTER_API_TOKEN")
        self.puter_model = os.getenv("PUTER_MODEL", "gpt-5.4-nano")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model = os.getenv(
            "OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
        self.llm7_key = os.getenv("LLM7_API_KEY")
        self.llm7_model = os.getenv("LLM7_MODEL", "gemini-3.1-flash-lite")
        self.pollinations_model = os.getenv("POLLINATIONS_MODEL", "openai")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if self.gemini_api_key and _HAS_GENAI:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.gemini_model = None

        # Last provider that successfully answered (for tagging / debugging)
        self.last_provider: Optional[str] = None

    # ------------------------------------------------------------------
    # Registry helpers
    # ------------------------------------------------------------------
    def list_providers(self) -> List[Dict]:
        """Provider metadata + availability for the /providers endpoint."""
        out = []
        for p in PROVIDERS:
            available = True
            if p["needs_key"]:
                available = bool(os.getenv(p["env_key"]))
            # g4f-backed entries need the package installed
            if p["id"].startswith("g4f-") and not _HAS_G4F:
                available = False
            if p["id"] == "gemini" and self.gemini_model is None:
                available = False
            out.append({**p, "available": available})
        return out

    def _chain(self, only: Optional[str] = None) -> List[str]:
        """Ordered provider ids to try. `only` restricts to one provider."""
        ids = [p["id"] for p in PROVIDERS]
        if only:
            if only not in ids:
                raise ValueError(f"Unknown provider: {only}")
            return [only]
        # Skip key-based providers whose key is missing
        avail = {p["id"] for p in self.list_providers() if p["available"]}
        return [i for i in ids if i in avail]

    # ------------------------------------------------------------------
    # Individual provider implementations (each returns full text)
    # ------------------------------------------------------------------
    async def _pollinations(self, messages: List[Dict]) -> str:
        url = "https://text.pollinations.ai/"
        payload = {"messages": messages, "model": self.pollinations_model,
                   "private": True}
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            # Plain-text response on the classic endpoint
            text = resp.text.strip()
            if not text:
                raise RuntimeError("Pollinations returned empty response")
            return text

    async def _llm7(self, messages: List[Dict]) -> str:
        url = "https://api.llm7.io/v1/chat/completions"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {self.llm7_key}"}
        payload = {"model": self.llm7_model, "messages": messages}
        return await _post_openai_compatible(url, headers, payload)

    async def _g4f(self, messages: List[Dict], model: str) -> str:
        if not _HAS_G4F:
            raise RuntimeError("g4f package not installed")
        response = await g4f.ChatCompletion.create_async(
            model=model, messages=messages)
        text = str(response).strip()
        if not text:
            raise RuntimeError(f"g4f {model} returned empty response")
        return text

    async def _puter(self, messages: List[Dict]) -> str:
        url = "https://api.puter.com/puterai/openai/v1/chat/completions"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {self.puter_token}"}
        payload = {"model": self.puter_model, "messages": messages}
        return await _post_openai_compatible(url, headers, payload)

    async def _groq(self, messages: List[Dict]) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {self.groq_key}"}
        payload = {"model": self.groq_model, "messages": messages}
        return await _post_openai_compatible(url, headers, payload)

    async def _openrouter(self, messages: List[Dict]) -> str:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {self.openrouter_key}",
                   "HTTP-Referer": "https://apps.visionquantech.com/omni-search/",
                   "X-Title": "Omni Search v4"}
        payload = {"model": self.openrouter_model, "messages": messages}
        return await _post_openai_compatible(url, headers, payload)

    async def _gemini(self, messages: List[Dict]) -> str:
        if self.gemini_model is None:
            raise RuntimeError("Gemini not configured (GEMINI_API_KEY missing)")
        prompt = messages[-1]["content"] if messages else ""
        res = await asyncio.to_thread(
            self.gemini_model.generate_content, prompt)
        text = (res.text or "").strip()
        if not text:
            raise RuntimeError("Gemini returned empty response")
        return text

    async def _call_once(self, provider_id: str, messages: List[Dict]) -> str:
        """Single attempt against one provider. Raises on failure."""
        if provider_id == "pollinations":
            return await self._pollinations(messages)
        if provider_id == "llm7":
            return await self._llm7(messages)
        if provider_id == "g4f-gpt4":
            return await self._g4f(messages, "gpt-4")
        if provider_id == "g4f-gpt35":
            return await self._g4f(messages, "gpt-3.5-turbo")
        if provider_id == "puter":
            return await self._puter(messages)
        if provider_id == "groq":
            return await self._groq(messages)
        if provider_id == "openrouter":
            return await self._openrouter(messages)
        if provider_id == "gemini":
            return await self._gemini(messages)
        raise ValueError(f"Unknown provider: {provider_id}")

    # ------------------------------------------------------------------
    # Streaming variants — yield small chunks for a live feel
    # ------------------------------------------------------------------
    async def _stream_once(self, provider_id: str, messages: List[Dict]):
        """Yield chunks from one provider. Tries SSE first, falls back to
        full-text split into chunks."""
        sse_providers = {
            "llm7": ("https://api.llm7.io/v1/chat/completions",
                     {"Content-Type": "application/json",
                      "Authorization": f"Bearer {self.llm7_key}"},
                     self.llm7_model),
            "puter": ("https://api.puter.com/puterai/openai/v1/chat/completions",
                      {"Content-Type": "application/json",
                       "Authorization": f"Bearer {self.puter_token}"},
                      self.puter_model),
            "groq": ("https://api.groq.com/openai/v1/chat/completions",
                     {"Content-Type": "application/json",
                      "Authorization": f"Bearer {self.groq_key}"},
                     self.groq_model),
            "openrouter": ("https://openrouter.ai/api/v1/chat/completions",
                           {"Content-Type": "application/json",
                            "Authorization": f"Bearer {self.openrouter_key}",
                            "HTTP-Referer": "https://apps.visionquantech.com/omni-search/",
                            "X-Title": "Omni Search v4"},
                           self.openrouter_model),
        }
        if provider_id in sse_providers:
            url, headers, model = sse_providers[provider_id]
            payload = {"model": model, "messages": messages, "stream": True}
            got_any = False
            async for chunk in _stream_openai_compatible(url, headers, payload):
                got_any = True
                yield chunk
            if not got_any:
                raise RuntimeError(f"{provider_id} stream returned no chunks")
            return

        # Non-SSE providers: fetch full text, then emit in chunks
        text = await self._call_once(provider_id, messages)
        for i in range(0, len(text), 120):
            yield text[i:i + 120]
            await asyncio.sleep(0.01)

    # ------------------------------------------------------------------
    # Public API (backward-compatible signatures + optional provider)
    # ------------------------------------------------------------------
    async def generate_stream_response(self, messages: list,
                                       provider: Optional[str] = None):
        """Streams with multi-tier fallback. Yields `__PROVIDER__:<id>` first."""
        prompt = messages[-1]["content"] if isinstance(messages, list) else str(messages)
        msgs = messages if isinstance(messages, list) else [
            {"role": "user", "content": prompt}]

        chain = self._chain(only=provider)
        for pid in chain:
            try:
                first = True
                async for chunk in self._stream_once(pid, msgs):
                    if first:
                        yield f"__PROVIDER__:{pid}\n"
                        first = False
                    if any(err in str(chunk)
                           for err in ["Response 429", "rate limit"]):
                        raise RuntimeError("rate limited")
                    yield chunk
                    await asyncio.sleep(0.005)
                if first:
                    # Provider yielded nothing — try next
                    continue
                self.last_provider = pid
                return
            except Exception as e:
                print(f"Provider {pid} failed: {e}")
                continue

        yield "\n\n[SYSTEM ERROR]: All AI providers currently unavailable."

    async def generate_response(self, messages: list,
                                provider: Optional[str] = None) -> str:
        """Non-streaming version with failover. Returns plain text."""
        prompt = messages[-1]["content"] if isinstance(messages, list) else str(messages)
        msgs = messages if isinstance(messages, list) else [
            {"role": "user", "content": prompt}]

        chain = self._chain(only=provider)
        for pid in chain:
            try:
                text = await self._call_once(pid, msgs)
                self.last_provider = pid
                return text
            except Exception as e:
                print(f"Provider {pid} failed: {e}")
                continue
        return "Error: No providers available."

    # Legacy aliases (kept for existing callers)
    async def stream_summary(self, prompt: str, provider: Optional[str] = None):
        async for chunk in self.generate_stream_response(
                [{"role": "user", "content": prompt}], provider=provider):
            yield chunk

    async def generate_full(self, prompt: str, provider: Optional[str] = None):
        return await self.generate_response(
            [{"role": "user", "content": prompt}], provider=provider)


sentinel = SentinelProvider()
