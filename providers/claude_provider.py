import os

import anthropic

from providers.base import BaseProvider

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024


class ClaudeProvider(BaseProvider):
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=api_key)

    def send(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text
