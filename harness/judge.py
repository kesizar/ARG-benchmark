"""Judge. This module is the only place that reads judge/ files."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


def _checkpoint_role(item: dict) -> str:
    role = str(item.get("role") or "critical")
    if role not in {"critical", "optional", "diagnostic"}:
        return "critical"
    return role


def _critical_checkpoints(cfg: dict) -> list[dict]:
    return [item for item in (cfg.get("checkpoints") or []) if _checkpoint_role(item) == "critical"]


_TIER_RANK = {"bad": 1, "normal": 2, "good": 3}


def _tier_rank(route: dict) -> int:
    return _TIER_RANK.get(str(route.get("tier") or ""), 0)


def _route_gates(route: dict) -> set[str]:
    ids = {str(item) for item in (route.get("gates") or []) if item}
    for group in route.get("gate_groups") or []:
        ids.update(group["ids"])
    return ids


def _route_counts(route: dict, reached: set[str]) -> tuple[int, int]:
    fixed = {str(item) for item in (route.get("gates") or []) if item}
    hits, total = len(fixed & reached), len(fixed)
    for group in route.get("gate_groups") or []:
        required = group["required"]
        hits += min(required, len(set(group["ids"]) & reached))
        total += required
    return hits, total


def _validate_gate_groups(cfg: dict) -> None:
    critical = {str(item["id"]) for item in _critical_checkpoints(cfg)}
    for route in cfg.get("routes") or []:
        if not route.get("gate_groups"):
            continue
        used = set(route.get("gates") or [])
        if not used <= critical:
            raise ValueError("Grouped route gates must reference critical checkpoints")
        for group in route["gate_groups"]:
            ids, required = group.get("ids"), group.get("required")
            if not isinstance(ids, list) or not ids or any(not isinstance(x, str) for x in ids):
                raise ValueError("gate_groups.ids must be a nonempty list of checkpoint IDs")
            if len(set(ids)) != len(ids) or used & set(ids):
                raise ValueError("gate_groups must not duplicate or overlap checkpoint IDs")
            if type(required) is not int or not 1 <= required <= len(ids):
                raise ValueError("gate_groups.required must be between 1 and the group size")
            if not set(ids) <= critical:
                raise ValueError("gate_groups must reference critical checkpoints")
            used.update(ids)


def _optional_checkpoint_ids(cfg: dict) -> list[str]:
    return [
        str(item.get("id"))
        for item in (cfg.get("checkpoints") or [])
        if isinstance(item, dict) and item.get("id") and _checkpoint_role(item) == "optional"
    ]


def norm_answer(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "")
    return "".join(normalized.split()).lower()


def answer_sha256(text: str) -> str:
    return hashlib.sha256(norm_answer(text).encode("utf-8")).hexdigest()


class Judge:
    def __init__(self, judge_cfg: dict | None, task_id: str, root: Path | None = None):
        self.cfg = judge_cfg or {}
        _validate_gate_groups(self.cfg)
        self.protocol = self.cfg.get("scoring_protocol", "legacy")
        if self.protocol not in {"legacy", "target_v1"}:
            raise ValueError("未知评分协议")
        if self.protocol == "target_v1":
            target = self.cfg.get("target_success")
            if not isinstance(target, dict) or not target:
                raise ValueError("target_v1 必须明确配置 target_success")
            route_ids = target.get("route_ids", [])
            if not isinstance(route_ids, list) or any(not isinstance(x, str) for x in route_ids):
                raise ValueError("target_success.route_ids 必须为字符串列表")
            routes = {str(r.get("id")): r for r in self.cfg.get("routes", []) if isinstance(r, dict)}
            if len(set(route_ids)) != len(route_ids) or any(x not in routes for x in route_ids):
                raise ValueError("target_success.route_ids 存在重复或未知路线")
            if any(str(routes[x].get("tier")) == "bad" for x in route_ids):
                raise ValueError("坏结局不能作为目标成功路线")
            critical = {str(item["id"]) for item in _critical_checkpoints(self.cfg)}
            if any(not _route_gates(routes[x]) <= critical for x in route_ids):
                raise ValueError("目标路线的门必须属于 critical checkpoint")
            for key in ("answer", "ending"):
                if key in target and type(target[key]) is not bool:
                    raise ValueError(f"target_success.{key} 必须为布尔值")
            if target.get("ending") and (routes or not isinstance(self.cfg.get("ending"), dict)):
                raise ValueError("target_success.ending 仅适用于单结局配置")
            condition = target.get("hook_condition")
            if condition is not None:
                if (not isinstance(condition, dict) or set(condition) != {"hook", "op"}
                        or condition.get("op") != "truthy"
                        or condition.get("hook") not in (self.cfg.get("hooks") or {})):
                    raise ValueError("target_success.hook_condition must reference a known truthy hook")
            if not (route_ids or target.get("answer") is True or target.get("ending") is True or condition):
                raise ValueError("target_success 必须包含明确的成功条件")
        self.task_id = task_id
        self.root = root or Path(".")
        self.available = judge_cfg is not None
        self.error = None if judge_cfg is not None else "裁判文件不可用"
        self.values: dict[str, Any] = {}
        self.prev_values: dict[str, Any] = {}
        self.checkpoints: dict[str, int] = {}
        self.side: dict[str, int] = {}
        self.events: list[dict[str, Any]] = []
        self.milestones: dict[str, int] = {}
        self.ending_reached = False
        self.game_ending_reached = False
        self.target_hook_reached = False
        self.ending_step: int | None = None
        self.failure_id: str | None = None
        self.failure_step: int | None = None
        self.route_endings: dict[str, int] = {}
        self.distinct: dict[str, set[str]] = {}
        self.maxima: dict[str, float] = {}
        self.conclusions: list[dict[str, Any]] = []
        self.answer_attempts = 0
        self.answer_correct = False

    @classmethod
    def load(cls, path: Path, task_id: str, root: Path) -> "Judge":
        file_path = Path(path)
        if not file_path.is_file():
            judge = cls(None, task_id, root)
            judge.error = f"找不到裁判文件 {file_path}"
            return judge
        return cls(json.loads(file_path.read_text(encoding="utf-8")), task_id, root)

    async def read(self, harness) -> dict[str, Any]:
        if not self.available:
            return {"error": self.error}
        values: dict[str, Any] = {}
        for name, hook in (self.cfg.get("hooks") or {}).items():
            if getattr(harness, "pending", None) and hook.get("type") in {
                "dom_regex", "localstorage", "js_truthy", "input_sha256"
            }:
                values[name] = self.values.get(name)
            else:
                values[name] = await self._eval_hook(name, hook, harness)
        for item in self.cfg.get("request_milestones") or []:
            values[f"milestone:{item.get('id')}"] = self._milestone_now(item, harness)
        self.values = values
        return values

    def update(self, step: int) -> list[tuple[str, str]]:
        if not self.available:
            return []
        fresh: list[tuple[str, str]] = []
        for item in self.cfg.get("checkpoints") or []:
            ident = str(item["id"])
            if not self._op_ok(self.values.get(item.get("hook")), item):
                continue
            if _checkpoint_role(item) != "critical":
                if ident not in self.side:
                    self.side[ident] = step
                    fresh.append(("diagnostic", ident))
                continue
            if ident in self.checkpoints:
                continue
            self.checkpoints[ident] = step
            fresh.append(("checkpoint", ident))
        for ident, spec in (self.cfg.get("events") or {}).items():
            hook = spec.get("hook")
            current = self._op_ok(self.values.get(hook), spec)
            previous = self._op_ok(self.prev_values.get(hook), spec)
            if current and not previous:
                self.events.append({"id": ident, "step": step})
                fresh.append(("event", str(ident)))
        # Failures are terminal outcomes, but never successful completions.
        # Opt-in preserves the semantics of existing judge files.
        if not self.ending_reached and self.failure_id is None:
            for failure in self.cfg.get("terminal_failures") or []:
                ident = str(failure.get("id") or "")
                if ident and self._op_ok(self.values.get(failure.get("hook")), failure):
                    self.failure_id = ident
                    self.failure_step = step
                    fresh.append(("failure", ident))
                    break
        condition = (self.cfg.get("target_success") or {}).get("hook_condition") if self.protocol == "target_v1" else None
        if self.failure_id is None and condition and not self.target_hook_reached:
            if self._op_ok(self.values.get(condition["hook"]), condition):
                self.target_hook_reached = True
                fresh.append(("target", str(condition["hook"])))
        if self.failure_id is not None:
            pass
        elif self._explicit_routes():
            for route in self._explicit_routes():
                ident = str(route.get("id") or "")
                ending = route.get("ending")
                if not ident or not ending or ident in self.route_endings:
                    continue
                if not self._route_ending_ok(route):
                    continue
                self.route_endings[ident] = step
                self.ending_reached = True
                self.game_ending_reached = True
                if self.ending_step is None:
                    self.ending_step = step
                fresh.append(("ending", ident))
        else:
            ending = self.cfg.get("ending")
            if ending and not self.ending_reached and self._op_ok(self.values.get(ending.get("hook")), ending):
                self.ending_reached = True
                self.game_ending_reached = True
                self.ending_step = step
                fresh.append(("ending", str(ending.get("hook") or "ending")))
        for item in self.cfg.get("request_milestones") or []:
            ident = str(item.get("id") or "")
            if not ident or ident in self.milestones:
                continue
            if self.values.get(f"milestone:{ident}"):
                self.milestones[ident] = step
                fresh.append(("milestone", ident))
        self.prev_values = dict(self.values)
        return fresh

    def score(self) -> dict[str, Any]:
        total = len(_critical_checkpoints(self.cfg)) if self.available else 0
        route = self._selected_route()
        tier = None
        if self.failure_id is not None:
            tier = None
        elif self.answer_correct:
            tier = "good"
        elif route is not None and str(route.get("id") or "") in self.route_endings:
            tier = str(route.get("tier") or "") or None
        elif route is not None and not self._explicit_routes() and (self.ending_reached or self.answer_correct):
            tier = "good"
        success = self._target_success() if self.protocol == "target_v1" else None
        return {
            "checkpoints_reached": len(self.checkpoints),
            "checkpoints_total": total,
            "checkpoints": dict(self.checkpoints),
            "diagnostic": dict(self.side),
            "route_id": None if route is None else str(route.get("id") or ""),
            "route_progress": self._target_progress(success) if self.protocol == "target_v1" else self._route_progress(route),
            "scoring_protocol": self.protocol,
            "target_success": success,
            "ending_reached": (self.ending_reached or self.answer_correct) and self.failure_id is None,
            "failure_reached": self.failure_id is not None,
            "failure_id": self.failure_id,
            "failure_step": self.failure_step,
            "ending_tier": tier,
            "good_ending": tier == "good",
            "ending_step": self.ending_step,
            "events": list(self.events),
            "milestones": dict(self.milestones),
            "answer_correct": self.answer_correct,
            "judge_error": self.error,
        }

    def _target_success(self) -> bool:
        if self.failure_id is not None:
            return False
        target = self.cfg["target_success"]
        return bool(
            (target.get("answer") is True and self.answer_correct)
            or (target.get("ending") is True and self.game_ending_reached)
            or any(ident in self.route_endings for ident in target.get("route_ids", []))
            or self.target_hook_reached
        )

    def _target_progress(self, success: bool) -> float | None:
        if success:
            return 1.0
        routes = self._explicit_routes()
        if not routes and self.cfg["target_success"].get("ending") is True:
            routes = [{"gates": [str(item["id"]) for item in _critical_checkpoints(self.cfg)]}]
        elif not routes:
            routes = []
        values = []
        for route in routes:
            hits, total = _route_counts(route, set(self.checkpoints))
            if total > 0:
                values.append(hits / (total + 1))
        return max(values) if values else None

    def _route_ending_ok(self, route: dict) -> bool:
        specs = []
        ending = route.get("ending")
        if isinstance(ending, dict):
            specs.append(ending)
        specs.extend(item for item in (route.get("any_of") or []) if isinstance(item, dict))
        return any(self._op_ok(self.values.get(spec.get("hook")), spec) for spec in specs)

    def _explicit_routes(self) -> list[dict]:
        return [item for item in (self.cfg.get("routes") or []) if isinstance(item, dict)]

    def _selected_route(self) -> dict | None:
        routes = self._explicit_routes()
        if not routes:
            gates = [str(item["id"]) for item in _critical_checkpoints(self.cfg)]
            ending = self.cfg.get("ending")
            if not gates and not ending and not self.answer_correct:
                return None
            return {"id": "main", "tier": "good", "gates": gates, "ending": ending}
        reached = set(self.checkpoints)
        matched = [route for route in routes if str(route.get("id") or "") in self.route_endings]
        if matched:
            return max(matched, key=lambda route: self._match_key(route, reached))
        live = []
        for route in routes:
            gates = _route_gates(route)
            if not gates:
                continue
            if not route.get("gate_groups") and any(
                not other.get("gate_groups") and gates < _route_gates(other) for other in routes
            ):
                continue
            live.append(route)
        if not live:
            return None
        return max(live, key=lambda route: self._open_key(route, reached))

    def _match_key(self, route: dict, reached: set[str]) -> tuple:
        hits, total = _route_counts(route, reached)
        ratio = hits / total if total else 1.0
        return (_tier_rank(route), hits, ratio)

    def _open_key(self, route: dict, reached: set[str]) -> tuple:
        hits, total = _route_counts(route, reached)
        return (hits, hits / total if total else 0.0)

    def _route_progress(self, route: dict | None) -> float | None:
        optional = _optional_checkpoint_ids(self.cfg)
        if route is None:
            if self.ending_reached or self.route_endings or not optional:
                return None
            hits = len(set(self.side) & set(optional))
            return round(hits / len(optional), 4)
        gates = _route_gates(route)
        gate_hits, gate_total = _route_counts(route, set(self.checkpoints))
        ident = str(route.get("id") or "")
        ended = ident in self.route_endings or (not self._explicit_routes() and self.ending_reached)
        if ended:
            if not gate_total:
                return 1.0
            return round(gate_hits / gate_total, 4)
        extra = [item for item in optional if item not in gates]
        denom = gate_total + len(extra)
        if denom == 0:
            return None
        hits = gate_hits + len(set(self.side) & set(extra))
        return round(hits / denom, 4)

    def check_answer(self, text: str) -> str:
        limit = int((self.cfg.get("max_answer_submits") or 0) or 0)
        if limit and self.answer_attempts >= limit:
            return "提交次数已用尽"
        self.answer_attempts += 1
        digest = answer_sha256(text)
        hashes = self._answer_hashes()
        if digest in hashes:
            self.answer_correct = True
            self.ending_reached = True
            return "正确"
        return "不正确"

    def record_conclusion(self, payload: dict) -> str:
        block = self.cfg.get("submit_conclusion") or {}
        if not block.get("enabled"):
            return "动作未启用"
        self.conclusions.append(payload)
        return "已记录"

    def markers(self) -> list[str]:
        names = list((self.cfg.get("hooks") or {}).keys())
        names.extend(str(item.get("id")) for item in (self.cfg.get("checkpoints") or []))
        names.extend(str(item) for item in (self.cfg.get("events") or {}))
        return [name for name in names if name]

    async def _eval_hook(self, name: str, hook: dict, harness) -> Any:
        kind = hook.get("type")
        if kind == "url_regex":
            urls = await harness.urls()
            return any(re.search(hook["pattern"], url) for url in urls)
        if kind == "tab_count":
            return harness.tab_count()
        if kind == "dialog_regex":
            messages = "\n".join(item.get("message") or "" for item in harness.dialogs_step())
            return bool(re.search(hook["pattern"], messages))
        if kind == "request_regex":
            return self._request_match(hook, harness)
        if kind == "localstorage":
            return await self._local_storage(hook, harness)
        if kind == "dom_regex":
            return await self._dom(name, hook, harness)
        if kind == "if_score":
            return harness.if_status().get("score")
        if kind == "if_victory":
            return bool(harness.if_status().get("victory"))
        if kind == "if_game_over":
            return bool(harness.if_status().get("game_over"))
        if kind == "state":
            data = harness.state() if hasattr(harness, "state") else {}
            if not isinstance(data, dict):
                return None
            return _json_path(data, str(hook.get("path") or ""))
        if kind == "input_sha256":
            reader = getattr(harness, "input_hashes", None)
            if reader is None:
                return False
            found = await reader(hook.get("selector"))
            wanted = {str(item).lower() for item in (hook.get("hashes") or []) if item}
            if not isinstance(found, (set, list, tuple)):
                return False
            return bool(wanted & {str(item).lower() for item in found})
        if kind == "js_strict_truthy":
            reader = getattr(harness, "strict_page_expr", None)
            if reader is None:
                raise RuntimeError("strict judge reader unavailable")
            return await reader(str(hook.get("expr") or ""))
        if kind == "js_truthy":
            reader = getattr(harness, "page_expr", None)
            if reader is None:
                return False
            return bool(await reader(str(hook.get("expr") or "")))
        return None

    async def _dom(self, name: str, hook: dict, harness) -> Any:
        pattern = re.compile(hook["pattern"])
        texts = await harness.dom_texts()
        per_frame = []
        matches: list[str] = []
        for text in texts:
            found = [item.group(0) for item in pattern.finditer(text or "")]
            per_frame.append(found)
            matches.extend(found)
        excludes = [re.compile(item) for item in hook.get("exclude") or []]
        if excludes:
            matches = [item for item in matches if not any(rule.search(item) for rule in excludes)]
        if hook.get("accumulate") == "distinct":
            self.distinct.setdefault(name, set()).update(matches)
            matches = sorted(self.distinct[name])
        agg = hook.get("agg") or "any"
        if agg == "count":
            value: Any = len(matches)
        elif agg == "max":
            numbers = [_number(item) for item in matches if _number(item) is not None]
            value = max(numbers) if numbers else (len(matches) if matches else 0)
        elif agg == "last":
            value = matches[-1] if matches else ""
        elif agg == "all":
            value = bool(per_frame) and all(frame for frame in per_frame)
        else:
            value = bool(matches)
        if hook.get("keep_max"):
            numeric = value if isinstance(value, (int, float)) else (len(matches) if matches else 0)
            self.maxima[name] = max(self.maxima.get(name, numeric), float(numeric))
            return self.maxima[name]
        return value

    async def _local_storage(self, hook: dict, harness) -> Any:
        data = await harness.local_storage(hook.get("frame_url_regex"))
        key = str(hook.get("key") or "")
        mode = hook.get("mode") or hook.get("read") or "exists"
        if mode == "exists":
            return key in data
        raw = data.get(key)
        if raw is None:
            return 0 if mode in {"length", "json_len"} else None
        if mode == "length":
            return len(raw)
        if mode == "hash":
            return hashlib.sha256(raw.encode("utf-8")).hexdigest()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if mode == "json_len":
            return len(parsed) if isinstance(parsed, (list, dict, str)) else 0
        if mode == "json_path":
            return _json_path(parsed, str(hook.get("path") or ""))
        return raw

    def _request_match(self, hook: dict, harness) -> bool:
        scope = hook.get("scope") or "all"
        rows = harness.requests("step" if scope == "step" else "all")
        types = set(hook.get("resource_types") or [])
        pattern = re.compile(hook["pattern"])
        for row in rows:
            if types and row.get("resource_type") not in types:
                continue
            if pattern.search(row.get("url") or ""):
                return True
        return False

    def _milestone_now(self, item: dict, harness) -> bool:
        return self._request_match(
            {
                "pattern": item.get("url_regex") or item.get("pattern") or "$^",
                "scope": "all",
                "resource_types": item.get("resource_types") or [],
            },
            harness,
        )

    def _answer_hashes(self) -> set[str]:
        hashes = set()
        inline = self.cfg.get("answer_sha256") or []
        if isinstance(inline, str):
            inline = [inline]
        hashes.update(item.lower() for item in inline if item)
        relative = self.cfg.get("answer_hash_file")
        if not relative:
            return hashes
        path = Path(relative)
        if not path.is_file():
            path = self.root / relative
        if not path.is_file():
            return hashes
        for line in path.read_text(encoding="utf-8").splitlines():
            token = line.strip().split()[-1] if line.strip() else ""
            if re.fullmatch(r"[0-9a-fA-F]{64}", token):
                hashes.add(token.lower())
        return hashes

    @staticmethod
    def _truthy(value: Any) -> bool:
        return bool(value) and value != "0"

    def _op_ok(self, value: Any, spec: dict) -> bool:
        op = spec.get("op") or "truthy"
        if op == "truthy":
            return self._truthy(value)
        if op == "eq":
            return value == spec.get("value")
        if op == "gte":
            try:
                return float(value) >= float(spec["value"])
            except (TypeError, ValueError):
                return False
        if op == "lte":
            try:
                return float(value) <= float(spec["value"])
            except (TypeError, ValueError):
                return False
        if op == "includes":
            return isinstance(value, list) and spec.get("value") in value
        return False


def _number(text: str) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _json_path(value: Any, path: str) -> Any:
    current = value
    for part in [item for item in path.split(".") if item]:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            if index >= len(current):
                return None
            current = current[index]
        else:
            return None
    return current
