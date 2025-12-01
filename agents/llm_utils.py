import time
from typing import Any, Callable, Optional


class LLMClientWrapper:
    """
    Wraps an LLM client and provides a retrying generate_content method.
    Expects the client to have generate_content(prompt) -> obj with .text
    """

    def __init__(
        self,
        client: Any,
        max_retries: int = 2,
        backoff_seconds: float = 1.0,
        on_error: Optional[Callable[[Exception, int], None]] = None,
    ):
        self.client = client
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.on_error = on_error

    def generate_text(self, prompt: str) -> str:
        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return self.client.generate_content(prompt).text
            except Exception as err:
                last_err = err
                if self.on_error:
                    self.on_error(err, attempt)
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * (2 ** attempt))
        if last_err:
            raise last_err
        return ""
