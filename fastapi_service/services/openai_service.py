"""Service-layer business logic for the book generation workflow."""

import time
from openai import OpenAI
from fastapi_service.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def complete(prompt: str, max_tokens: int = 3000) -> str:
    """Complete."""
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))

    raise RuntimeError(f"OpenAI call failed after {MAX_RETRIES} attempts: {last_error}")