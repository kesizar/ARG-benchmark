"""Replay a fixed action list. Extra steps become give_up."""

from __future__ import annotations


class ScriptedPolicy:
    def __init__(self, actions: list[dict] | None) -> None:
        self.actions = list(actions or [])
        self.index = 0

    def act(self, obs: dict) -> dict:
        del obs
        if self.index >= len(self.actions):
            return {"op": "give_up"}
        action = self.actions[self.index]
        self.index += 1
        return dict(action)
