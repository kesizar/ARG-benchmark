"""Token totals for one episode."""

from __future__ import annotations


class TokenLedger:
    def __init__(self) -> None:
        self.prompt = 0
        self.completion = 0

    def add(self, prompt: int = 0, completion: int = 0) -> None:
        self.prompt += int(prompt or 0)
        self.completion += int(completion or 0)

    def as_dict(self) -> dict[str, int]:
        return {
            "prompt": self.prompt,
            "completion": self.completion,
            "total": self.prompt + self.completion,
        }
