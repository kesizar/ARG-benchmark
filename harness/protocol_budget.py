"""Task budget tiers chosen from a frozen, evidenced reference trajectory."""


def reference_limits(steps: int, answer_submits: int = 10) -> dict:
    if type(steps) is not int or steps < 1:
        raise ValueError("参考轨迹步数必须为正整数")
    if type(answer_submits) is not int or answer_submits < 10:
        raise ValueError("答案提交额度至少为 10")
    actions, seconds = ((60, 3600) if steps <= 20 else (150, 7200) if steps <= 50 else (300, 10800))
    return {"max_steps": actions, "max_seconds": seconds, "max_answer_submits": answer_submits}


def validate_budget(task: dict, cfg: dict) -> None:
    if not isinstance(task.get("reference_evidence"), str) or not task["reference_evidence"].strip():
        raise ValueError("必须提供参考轨迹证据")
    answer_submits = task.get("max_answer_submits", 10)
    if answer_submits != 10:
        required = task.get("required_answer_submits")
        if not isinstance(task.get("answer_budget_evidence"), str) or not task["answer_budget_evidence"].strip():
            raise ValueError("增加答案提交额度必须提供证据")
        if type(required) is not int or required <= 10 or answer_submits != required + 2:
            raise ValueError("增加的提交额度须为已验证所需次数加 2")
    expected = reference_limits(task.get("reference_steps"), answer_submits)
    if "max_steps_override" in task:
        override = task["max_steps_override"]
        reason = task.get("step_budget_override_reason")
        if type(override) is not int or override < task["reference_steps"]:
            raise ValueError("单题动作上限须为不低于参考步数的整数")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("单题动作上限调整必须提供理由")
        expected["max_steps"] = override
    if any((cfg.get("limits") or {}).get(key) != value for key, value in expected.items()):
        raise ValueError("任务预算与冻结清单的参考轨迹档位或单题上限不一致")
