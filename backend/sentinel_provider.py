import os
import g4f
import asyncio
import google.generativeai as genai
from typing import AsyncGenerator, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class SentinelProvider:
    """
    Industry-grade LLM orchestrator with automatic failover.
    Ensures 'Omni' never goes down.
    """
    def __init__(self):
        # Configure Gemini if API key is in environment (fallback to free g4f otherwise)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_model = None

    async def _call_g4f_generic(self, prompt: str, model: str):
        """Generic G4F caller."""
        try:
            return g4f.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
        except Exception as e:
            print(f"G4F {model} error: {e}")
            raise

    async def generate_stream_response(self, messages: list) -> AsyncGenerator[str, None]:
        """Streams with multi-tier fallback (GPT-4 -> GPT-3.5 -> Gemini)."""
        prompt = messages[-1]["content"] if isinstance(messages, list) else str(messages)
        
        trials = [
            ("GPT-4 (Free)", "gpt-4"),
            ("GPT-3.5 (Stable Free)", "gpt-3.5-turbo")
        ]

        for name, model in trials:
            try:
                response = await self._call_g4f_generic(prompt, model)
                if not response: continue
                
                first_chunk_found = False
                for message in response:
                    if message:
                        msg_str = str(message)
                        if any(err in msg_str for err in ["Response 429", "rate limit"]): break
                        yield msg_str
                        first_chunk_found = True
                        await asyncio.sleep(0.01)
                if first_chunk_found: return
            except Exception: continue

        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(prompt, stream=True)
                for chunk in response:
                    if chunk.text: yield chunk.text
                return
            except Exception: pass

        yield "\n\n[SYSTEM ERROR]: All AI providers currently unavailable."

    async def generate_response(self, messages: list) -> str:
        """Non-streaming version with failover."""
        prompt = messages[-1]["content"] if isinstance(messages, list) else str(messages)
        try:
            response = await g4f.ChatCompletion.create_async(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
            )
            return str(response)
        except Exception:
            if self.gemini_model:
                try:
                    res = self.gemini_model.generate_content(prompt)
                    return res.text
                except Exception: pass
            return "Error: No providers available."

    # Legacy Aliases
    async def stream_summary(self, prompt: str):
        async for chunk in self.generate_stream_response([{"role": "user", "content": prompt}]):
            yield chunk

    async def generate_full(self, prompt: str):
        return await self.generate_response([{"role": "user", "content": prompt}])

sentinel = SentinelProvider()
