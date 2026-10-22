"""One AgentEscapeBench scenario, played in-process. Win ids stay out of the text."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HIDDEN_TYPES = {"Item", "Hidden_Item", "ITEM", "HIDDEN_ITEM"}
_BLOCKED_TOOLS = {"code_py_exec"}


class ScenarioHarness:
    def __init__(self, cfg: dict, run_dir: Path) -> None:
        self.cfg = cfg
        self.run_dir = run_dir
        self.data: dict = {}
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []
        self.revealed: set[str] = set()
        self.solved: set[str] = set()
        self.hidden_ready: set[str] = set()
        self.won = False
        self.win_node = ""
        self.last: dict = {}
        self.simulator = None
        self.blocked: list = []

    async def start(self) -> None:
        spec = self.cfg.get("scenario") or {}
        source = Path(spec.get("root") or "tasks/agent-escape-bench/src")
        case = Path(spec.get("file") or "")
        if not source.is_absolute():
            source = Path.cwd() / source
        if not case.is_absolute():
            case = Path.cwd() / case
        folder = str(source.resolve())
        if folder not in sys.path:
            sys.path.insert(0, folder)
        from simulator import ToolSimulator

        self.simulator = ToolSimulator()
        self.data = json.loads(case.read_text(encoding="utf-8"))
        self.nodes = {item["id"]: item for item in self.data.get("nodes") or []}
        self.edges = list(self.data.get("edges") or [])
        meta = self.data.get("metadata") or {}
        self.win_node = str(meta.get("win_node_id") or "")
        self.revealed = {item["id"] for item in self.nodes.values() if item.get("is_revealed") or item.get("initial_visible")}
        self.solved = set()
        self.hidden_ready = set()
        self.won = False
        self.last = {}

    async def close(self) -> None:
        return None

    async def reset(self) -> None:
        await self.start()

    async def observe(self, label: str | None = None) -> dict:
        del label
        return self._obs()

    async def act(self, action: dict) -> str:
        if action.get("op") in {"wait", "scroll", "back"}:
            return "ok"
        if action.get("op") != "call":
            return "动作未启用"
        name = str(action.get("name") or "")
        payload = action.get("object") or {}
        if name == "investigate":
            self.last = self._investigate(str(payload.get("node_id") or ""))
        elif name == "tool":
            self.last = self._tool(str(payload.get("node_id") or ""), payload.get("arguments") or {})
        elif name == "use_item":
            self.last = self._use_item(str(payload.get("node_id") or ""), payload.get("arguments") or {})
        else:
            return "动作未启用"
        return json.dumps(self.last, ensure_ascii=False)

    def state(self) -> dict:
        return {
            "revealed": sorted(self.revealed),
            "solved": sorted(self.solved),
            "won": self.won,
        }

    def _public(self) -> dict:
        meta = self.data.get("metadata") or {}
        entities = []
        for node_id in sorted(self.revealed):
            node = self.nodes[node_id]
            item = {"id": node_id, "type": node.get("type") or "", "can_investigate": True}
            if node.get("description"):
                item["description"] = node["description"]
            entities.append(item)
        information = []
        for init in (meta.get("initial_values") or {}).values():
            for value in (init.get("init_inputs") or {}).values():
                information.append({"value": value})
        view = {
            "narrative": (meta.get("intro_narrative") or ""),
            "available_entities": entities,
            "available_information": information,
        }
        if self.last:
            view["last_result"] = self.last
        return view

    def _obs(self) -> dict:
        return {
            "url": "",
            "visible_text": json.dumps(self._public(), ensure_ascii=False, indent=2),
            "elements": [],
            "tabs": [],
            "dialogs": [],
            "pending_dialog": None,
            "screenshot": "",
        }

    def _visible(self, node_id: str) -> dict | None:
        if node_id not in self.nodes or node_id not in self.revealed:
            return None
        return self.nodes[node_id]

    def _investigate(self, node_id: str) -> dict:
        node = self._visible(node_id)
        if node is None:
            return {"ok": False, "error": "还看不到这个东西"}
        revealed_now = []
        if node_id in self.hidden_ready:
            revealed_now.extend(self._drop(node_id, {"Hidden_Item", "HIDDEN_ITEM"}))
            self.hidden_ready.discard(node_id)
        if node.get("type") == "Item":
            revealed_now.extend(self._drop(node_id, {"Item", "Hidden_Item", "ITEM", "HIDDEN_ITEM"}))
        details = {
            "id": node_id,
            "type": node.get("type"),
            "description": node.get("description") or "",
            "narrative": node.get("narrative") or "",
            "inputs": self._input_ports(node),
            "outputs": [
                {"name": port.get("name"), "type": port.get("type"), "description": port.get("description") or ""}
                for port in node.get("outputs") or []
                if port.get("type") not in _HIDDEN_TYPES
            ],
        }
        result = {"ok": True, "details": details}
        if revealed_now:
            result["newly_revealed"] = revealed_now
        return result

    def _input_ports(self, node: dict) -> list[dict]:
        upstream = {
            edge.get("target_port")
            for edge in self.edges
            if edge.get("target_id") == node.get("id") and edge.get("connection_type") not in _HIDDEN_TYPES
        }
        has_edge = any(edge.get("target_id") == node.get("id") for edge in self.edges)
        ports = []
        for port in node.get("inputs") or []:
            if port.get("type") in _HIDDEN_TYPES:
                continue
            shown = {"name": port.get("name"), "type": port.get("type"), "description": port.get("description") or ""}
            if has_edge and port.get("name") not in upstream and port.get("value") is not None:
                shown["init_value"] = port.get("value")
            ports.append(shown)
        return ports

    def _tool(self, node_id: str, arguments: dict) -> dict:
        node = self._visible(node_id)
        if node is None or node.get("type") != "Tool":
            return {"ok": False, "error": "这个工具现在不能用"}
        template = str(node.get("template_id") or "")
        if template in _BLOCKED_TOOLS or self.simulator is None:
            return {"ok": False, "error": "这个工具不能用"}
        clean = {key: value for key, value in arguments.items() if not str(key).startswith("_")}
        try:
            output = self.simulator.execute(template, clean)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc).splitlines()[0][:180]}
        if not isinstance(output, dict):
            output = {}
        output.pop("_validation", None)
        matched = self._matches(node, clean, output)
        if matched:
            self.solved.add(node_id)
            self._drop(node_id, {"Item", "ITEM"})
            if any(edge.get("source_id") == node_id and edge.get("connection_type") in {"Hidden_Item", "HIDDEN_ITEM"} for edge in self.edges):
                self.hidden_ready.add(node_id)
            if node_id == self.win_node:
                self.won = True
        result = {"ok": True, "output_values": output, "solved": matched}
        if node_id in self.hidden_ready:
            result["investigate_hint"] = "这个工具好像还藏着东西，可以再查看一次。"
        return result

    def _use_item(self, node_id: str, arguments: dict) -> dict:
        node = self._visible(node_id)
        if node is None or node.get("type") != "Item":
            return {"ok": False, "error": "这个物品现在不能用"}
        expected = self._golden_inputs(node)
        clean = {key: value for key, value in arguments.items() if not str(key).startswith("_")}
        if expected and not self._same(expected, clean):
            return {"ok": False, "error": "参数不对"}
        self.solved.add(node_id)
        revealed_now = self._drop(node_id, {"Item", "Hidden_Item", "ITEM", "HIDDEN_ITEM"})
        result = {"ok": True, "narrative": node.get("narrative") or ""}
        if revealed_now:
            result["newly_revealed"] = revealed_now
        return result

    def _drop(self, node_id: str, kinds: set[str]) -> list[dict]:
        found = []
        for edge in self.edges:
            if edge.get("source_id") != node_id or edge.get("connection_type") not in kinds:
                continue
            target = edge.get("target_id")
            if not target or target not in self.nodes or target in self.revealed:
                continue
            self.revealed.add(target)
            node = self.nodes[target]
            found.append({"id": target, "type": node.get("type") or "", "description": node.get("description") or ""})
        return found

    def _matches(self, node: dict, arguments: dict, output: dict) -> bool:
        expected_in = self._golden_inputs(node)
        expected_out = {
            port.get("name"): port.get("value")
            for port in node.get("outputs") or []
            if port.get("type") not in _HIDDEN_TYPES and port.get("name") and "value" in port
        }
        if expected_in and not self._same(expected_in, arguments):
            return False
        if expected_out and not self._same(expected_out, output):
            return False
        return bool(expected_in or expected_out)

    def _golden_inputs(self, node: dict) -> dict:
        return {
            port.get("name"): port.get("value")
            for port in node.get("inputs") or []
            if port.get("type") not in _HIDDEN_TYPES and port.get("name") and "value" in port
        }

    def _same(self, expected: dict, actual: dict) -> bool:
        for key, value in expected.items():
            if str(actual.get(key)) != str(value):
                return False
        return True

    async def urls(self) -> list[str]:
        return []

    async def dom_texts(self) -> list[str]:
        return [self._obs()["visible_text"]]

    async def local_storage(self, frame_url_regex: str | None = None) -> dict:
        del frame_url_regex
        return {}

    def dialogs_step(self) -> list:
        return []

    def tab_count(self) -> int:
        return 0

    def requests(self, scope: str = "all") -> list:
        del scope
        return []

    def if_status(self) -> dict:
        return {}

    def consume_step(self) -> None:
        return None
