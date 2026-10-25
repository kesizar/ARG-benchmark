"""
Human Client - Flask 后端
为人类玩家提供与评测 server 交互的 Web 界面
支持多人同时在线（每个浏览器 Tab 通过 cookie client_id 隔离）
"""
import csv
import json
import os
import threading
import time
import uuid
from datetime import datetime

import requests
from flask import Flask, jsonify, make_response, request

app = Flask(__name__)

# ── 配置 ──────────────────────────────────────────────────────────────────────
SERVER_URL = os.environ.get("EVAL_SERVER_URL", "http://localhost:8000")

# 题目根目录：包含 5/ 10/ 15/ 三个子目录，每个子目录下有 narrative/ 文件夹
CASE_BASE_DIR = os.environ.get(
    "CASE_BASE_DIR",
    os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..",
        "data", "narrative_generate"
    ))
)

# 做题记录 CSV 文件路径（和 app.py 同目录）
RECORDS_CSV = os.path.join(os.path.dirname(__file__), "records.csv")
CSV_FIELDS = ["timestamp", "player_id", "case_file", "case_id",
              "start_time", "end_time", "steps", "success", "gave_up"]

# 难度 → 最少操作次数映射
GIVEUP_MIN_STEPS_MAP = {5: 35, 10: 80, 15: 130}
GIVEUP_MIN_STEPS_DEFAULT = 35

# ── 多用户会话存储 ─────────────────────────────────────────────────────────────
# { client_id: { ...session fields... } }
_sessions: dict = {}
_sessions_lock = threading.Lock()

# ── CSV 写锁（多人同时完成时避免并发写入损坏文件）────────────────────────────
_csv_lock = threading.Lock()


def _ensure_csv_header():
    """确保 CSV 文件存在且有表头"""
    if not os.path.exists(RECORDS_CSV):
        with open(RECORDS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()


_ensure_csv_header()


# ── 会话工具函数 ───────────────────────────────────────────────────────────────

def _new_session_state() -> dict:
    return {
        "player_id": None,
        "case_id": None,
        "case_file": None,       # 题目文件路径，用于记录
        "eval_session_id": None,  # 发给 eval server 的 session_id
        "step": 0,
        "action_count": 0,
        "giveup_min_steps": GIVEUP_MIN_STEPS_DEFAULT,
        "log": [],
        "entities": [],
        "info": [],
        "available_tools": [],
        "available_items_for_use": [],
        "win": False,
        "gave_up": False,
        "start_time": None,
    }


def _get_client_id() -> str:
    """从 Cookie 获取 client_id，若不存在则生成新的"""
    return request.cookies.get("client_id") or str(uuid.uuid4())


def _get_session(client_id: str) -> dict:
    """获取或创建对应 client_id 的 session"""
    with _sessions_lock:
        if client_id not in _sessions:
            _sessions[client_id] = _new_session_state()
        return _sessions[client_id]


def _inject_cookie(response, client_id: str):
    """把 client_id 写回 Cookie（仅在新建时需要）"""
    if not request.cookies.get("client_id"):
        response.set_cookie(
            "client_id", client_id,
            max_age=60 * 60 * 24 * 30,  # 30 天
            samesite="Lax",
            httponly=False,
        )
    return response


def _reset_session(sess: dict):
    """重置 session 到初始状态（保留 player_id）"""
    player_id = sess.get("player_id")
    sess.update(_new_session_state())
    sess["player_id"] = player_id


def _escape_for_display(val) -> str:
    """将值中的不可打印控制字符转为可见的转义形式，便于前端显示和复制。

    例如: '9374105826\n' → '9374105826\\n'
          '\x074R?U-'   → '\\x074R?U-'
    前端 unescapeInput() 会在用户提交时将这些转义还原为真实字符。
    """
    s = str(val)
    out = []
    for ch in s:
        cp = ord(ch)
        if cp == 0x0a:
            out.append('\\n')
        elif cp == 0x0d:
            out.append('\\r')
        elif cp == 0x09:
            out.append('\\t')
        elif cp <= 0x1f or cp == 0x7f:
            out.append(f'\\x{cp:02x}')
        else:
            out.append(ch)
    return ''.join(out)


def _add_log(sess: dict, role: str, content: str):
    sess["step"] += 1
    if role == "action":
        sess["action_count"] += 1
    sess["log"].append({
        "step": sess["step"],
        "role": role,
        "content": content,
        "time": datetime.now().strftime("%H:%M:%S"),
    })


def _update_entities(sess: dict, newly_revealed: list):
    if not newly_revealed:
        return
    existing_ids = {e["id"] for e in sess["entities"]}
    for entity in newly_revealed:
        if entity.get("id") and entity["id"] not in existing_ids:
            sess["entities"].append({
                "id": entity["id"],
                "type": entity.get("type", "Unknown"),
                "description": entity.get("description", ""),
            })
            existing_ids.add(entity["id"])


def _register_tool(sess: dict, details: dict):
    tool_id = details.get("id")
    if not tool_id:
        return
    ids = [t["id"] for t in sess["available_tools"]]
    if tool_id not in ids:
        sess["available_tools"].append({
            "id": tool_id,
            "description": details.get("description", ""),
            "inputs": details.get("inputs", []),
            "outputs": details.get("outputs", []),
        })


def _register_item_for_use(sess: dict, node_id: str, required_inputs: list):
    ids = [i["id"] for i in sess["available_items_for_use"]]
    if node_id not in ids:
        sess["available_items_for_use"].append({
            "id": node_id,
            "required_inputs": required_inputs,
        })


def _save_record(sess: dict, success: bool, gave_up: bool):
    """追加写入 CSV，同时更新内存 player_records（供 /api/records 接口使用）"""
    player_id = sess.get("player_id") or "anonymous"
    now = datetime.now().isoformat()
    row = {
        "timestamp": now,
        "player_id": player_id,
        "case_file": sess.get("case_file", ""),
        "case_id": sess.get("case_id", ""),
        "start_time": sess.get("start_time", ""),
        "end_time": now,
        "steps": sess["action_count"],
        "success": success,
        "gave_up": gave_up,
    }
    # 写 CSV
    with _csv_lock:
        with open(RECORDS_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writerow(row)
    # 写内存（供实时查询）
    with _sessions_lock:
        if player_id not in _player_records:
            _player_records[player_id] = []
        _player_records[player_id].append({
            "case_file": row["case_file"],
            "case_id": row["case_id"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "steps": row["steps"],
            "success": success,
            "gave_up": gave_up,
        })


# 内存中的做题历史（从 CSV 恢复 + 运行时追加）
_player_records: dict = {}


def _load_records_from_csv():
    """启动时从 CSV 恢复历史记录到内存"""
    if not os.path.exists(RECORDS_CSV):
        return
    try:
        with open(RECORDS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("player_id", "anonymous")
                if pid not in _player_records:
                    _player_records[pid] = []
                _player_records[pid].append({
                    "case_file": row.get("case_file", ""),
                    "case_id": row.get("case_id", ""),
                    "start_time": row.get("start_time", ""),
                    "end_time": row.get("end_time", ""),
                    "steps": int(row.get("steps", 0)),
                    "success": row.get("success", "False") == "True",
                    "gave_up": row.get("gave_up", "False") == "True",
                })
    except Exception as e:
        print(f"[WARN] 读取历史记录失败: {e}")


_load_records_from_csv()


# ── 路由 ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    html_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "index.html")
    client_id = _get_client_id()
    _get_session(client_id)  # 确保 session 存在
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    resp = make_response(html)
    _inject_cookie(resp, client_id)
    return resp


@app.route("/api/status")
def api_status():
    client_id = _get_client_id()
    sess = _get_session(client_id)
    data = {
        "player_id": sess["player_id"],
        "case_id": sess["case_id"],
        "step": sess["action_count"],
        "win": sess["win"],
        "gave_up": sess["gave_up"],
        "giveup_allowed": (
            sess["action_count"] >= sess["giveup_min_steps"]
            and not sess["win"]
            and not sess["gave_up"]
            and sess["case_id"] is not None
        ),
        "giveup_min_steps": sess["giveup_min_steps"],
        "entities": sess["entities"],
        "info": sess["info"],
        "available_tools": sess["available_tools"],
        "available_items_for_use": sess["available_items_for_use"],
        "log": sess["log"],
    }
    resp = make_response(jsonify(data))
    _inject_cookie(resp, client_id)
    return resp


@app.route("/api/set_player", methods=["POST"])
def api_set_player():
    client_id = _get_client_id()
    sess = _get_session(client_id)
    data = request.json or {}
    player_id = data.get("player_id", "").strip()
    if not player_id:
        return jsonify({"ok": False, "error": "player_id is required"}), 400
    sess["player_id"] = player_id
    resp = make_response(jsonify({"ok": True, "player_id": player_id}))
    _inject_cookie(resp, client_id)
    return resp


@app.route("/api/load_case", methods=["POST"])
def api_load_case():
    client_id = _get_client_id()
    sess = _get_session(client_id)
    data = request.json or {}
    case_file_path = data.get("case_file_path", "").strip()
    if not case_file_path:
        return jsonify({"ok": False, "error": "case_file_path is required"}), 400

    player_id = data.get("player_id", "").strip()
    if player_id:
        sess["player_id"] = player_id

    _reset_session(sess)
    eval_session_id = f"human_{client_id[:8]}_{int(time.time() * 1000)}"
    sess["eval_session_id"] = eval_session_id
    sess["case_file"] = case_file_path
    sess["start_time"] = datetime.now().isoformat()

    try:
        resp_ev = requests.post(
            f"{SERVER_URL}/env/reset",
            params={"case_file_path": case_file_path, "session_id": eval_session_id},
            timeout=30,
        )
        resp_ev.raise_for_status()
        result = resp_ev.json()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    if not result.get("ok"):
        return jsonify(result), 400

    sess["case_id"] = result["case_id"]

    # 根据 metadata.total_nodes 动态设置放弃阈值
    try:
        with open(case_file_path, "r", encoding="utf-8") as _f:
            _case_data = json.load(_f)
        _total_nodes = _case_data.get("metadata", {}).get("total_nodes", None)
        sess["giveup_min_steps"] = GIVEUP_MIN_STEPS_MAP.get(
            _total_nodes, GIVEUP_MIN_STEPS_DEFAULT
        )
    except Exception:
        sess["giveup_min_steps"] = GIVEUP_MIN_STEPS_DEFAULT

    for entity in result.get("available_entities", []):
        sess["entities"].append({
            "id": entity.get("id", ""),
            "type": entity.get("type", ""),
            "description": entity.get("description", ""),
        })

    for info in result.get("available_information", []):
        sess["info"].append(info)

    win_node = result.get("win_node_id", "")
    metadata_text = f"胜利节点: {win_node}" if win_node else ""
    narrative = result.get("narrative", "")
    _add_log(sess, "system", f"📖 **场景开篇**\n\n{narrative}\n\n{metadata_text}")

    resp = make_response(jsonify({"ok": True, "case_id": sess["case_id"]}))
    _inject_cookie(resp, client_id)
    return resp


@app.route("/api/giveup", methods=["POST"])
def api_giveup():
    client_id = _get_client_id()
    sess = _get_session(client_id)
    if not sess["case_id"]:
        return jsonify({"ok": False, "error": "No case loaded"}), 400
    if sess["win"]:
        return jsonify({"ok": False, "error": "Already won"}), 400
    if sess["gave_up"]:
        return jsonify({"ok": False, "error": "Already gave up"}), 400
    giveup_min = sess["giveup_min_steps"]
    if sess["action_count"] < giveup_min:
        return jsonify({
            "ok": False,
            "error": f"至少需要操作 {giveup_min} 次后才能放弃（当前: {sess['action_count']} 次）"
        }), 400

    sess["gave_up"] = True
    _add_log(sess, "system",
             f"🏳️ **放弃本题**\n做题者主动放弃，共操作 {sess['action_count']} 步（阈值 {sess['giveup_min_steps']} 步）。")
    _save_record(sess, success=False, gave_up=True)
    resp = make_response(jsonify({"ok": True, "steps": sess["action_count"]}))
    _inject_cookie(resp, client_id)
    return resp


@app.route("/api/records")
def api_records():
    """查询做题记录（内存 + CSV 均已同步）"""
    player_id = request.args.get("player_id", "").strip()
    if player_id:
        records = _player_records.get(player_id, [])
        return jsonify({"ok": True, "player_id": player_id, "records": records})
    return jsonify({"ok": True, "all_records": _player_records})


@app.route("/api/investigate", methods=["POST"])
def api_investigate():
    client_id = _get_client_id()
    sess = _get_session(client_id)
    if not sess["case_id"]:
        return jsonify({"ok": False, "error": "No case loaded"}), 400

    data = request.json or {}
    node_id = data.get("node_id", "").strip()
    if not node_id:
        return jsonify({"ok": False, "error": "node_id is required"}), 400

    _add_log(sess, "action", f"🔍 **investigate** `{node_id}`")

    try:
        resp_ev = requests.post(
            f"{SERVER_URL}/env/{sess['case_id']}/investigate",
            json={"node_id": node_id},
            timeout=30,
        )
        resp_ev.raise_for_status()
        result = resp_ev.json()
    except Exception as e:
        _add_log(sess, "feedback", f"❌ 请求失败: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

    feedback_lines = []
    if not result.get("ok"):
        feedback_lines.append(f"❌ **失败**: {result.get('error', 'Unknown error')}")
    else:
        entity_type = result.get("entity_type", "")
        if entity_type == "Tool":
            details = result.get("details", {})
            _register_tool(sess, details)
            feedback_lines.append(f"✅ **Tool 调查成功**: `{details.get('id')}`")
            if details.get("description"):
                feedback_lines.append(f"**描述**: {details['description']}")
            if details.get("narrative"):
                feedback_lines.append(f"**背景线索**: {details['narrative']}")
            if details.get("inputs"):
                inputs_parts = []
                for p in details["inputs"]:
                    part = f"`{p['name']}` ({p.get('type','?')})"
                    if p.get("upstream_from"):
                        part += f" ← 来自上游 `{p['upstream_from']}`"
                    elif "init_value" in p:
                        part += f" = `{_escape_for_display(p['init_value'])}`"
                    inputs_parts.append(part)
                feedback_lines.append(f"**输入参数**: {', '.join(inputs_parts)}")
            if details.get("outputs"):
                outputs_str = ", ".join(
                    f"`{p['name']}` ({p.get('type','?')})" for p in details["outputs"]
                )
                feedback_lines.append(f"**输出参数**: {outputs_str}")
            feedback_lines.append("→ 该工具现在可以直接调用")

        elif entity_type == "Item":
            if result.get("message"):
                feedback_lines.append(f"✓ {result['message']}")
            elif result.get("required_inputs"):
                required = result["required_inputs"]
                _register_item_for_use(sess, node_id, required)
                feedback_lines.append("⚠️ **Item 需要参数才能解锁**")
                params_str = ", ".join(
                    f"`{p['name']}` ({p.get('type','?')})" for p in required
                )
                feedback_lines.append(f"**必填参数**: {params_str}")
                if result.get("narrative"):
                    feedback_lines.append(f"**背景线索**: {result['narrative']}")
            elif "content" in result:
                content_val = result['content']
                if isinstance(content_val, dict):
                    for k, v in content_val.items():
                        feedback_lines.append(f"✅ **Item 内容[{k}]**: `{_escape_for_display(v)}`")
                else:
                    feedback_lines.append(f"✅ **Item 内容**: `{_escape_for_display(content_val)}`")
                if result.get("narrative"):
                    feedback_lines.append(f"**背景线索**: {result['narrative']}")
            else:
                feedback_lines.append("✅ **Item 调查成功**（纯触发器，无内容）")
                if result.get("narrative"):
                    feedback_lines.append(f"**背景线索**: {result['narrative']}")
        else:
            feedback_lines.append(f"✅ 调查完成: {json.dumps(result, ensure_ascii=False)}")

        if result.get("newly_revealed"):
            _update_entities(sess, result["newly_revealed"])
            names = [e.get("id", "") for e in result["newly_revealed"]]
            feedback_lines.append(f"🎁 **新发现实体**: {', '.join(names)}")

        if result.get("investigate_hints"):
            for hint in result["investigate_hints"]:
                feedback_lines.append(
                    f"💡 **探索提示** (工具 `{hint.get('tool_id','')}`): {hint.get('hint','')}"
                )

    _add_log(sess, "feedback", "\n".join(feedback_lines))
    resp = make_response(jsonify({"ok": True}))
    _inject_cookie(resp, client_id)
    return resp


@app.route("/api/tool_call", methods=["POST"])
def api_tool_call():
    client_id = _get_client_id()
    sess = _get_session(client_id)
    if not sess["case_id"]:
        return jsonify({"ok": False, "error": "No case loaded"}), 400

    data = request.json or {}
    node_id = data.get("node_id", "").strip()
    arguments = data.get("arguments", {})
    if not node_id:
        return jsonify({"ok": False, "error": "node_id is required"}), 400

    args_display = ", ".join(f"{k}={repr(v)}" for k, v in arguments.items())
    _add_log(sess, "action", f"⚙️ **tool_call** `{node_id}`\n参数: {args_display}")

    try:
        resp_ev = requests.post(
            f"{SERVER_URL}/env/{sess['case_id']}/tool_call",
            json={"node_id": node_id, "arguments": arguments},
            timeout=30,
        )
        resp_ev.raise_for_status()
        result = resp_ev.json()
    except Exception as e:
        _add_log(sess, "feedback", f"❌ 请求失败: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

    feedback_lines = []
    if not result.get("ok"):
        feedback_lines.append(f"❌ **失败**: {result.get('error', 'Unknown error')}")
    else:
        if "output_values" in result:
            feedback_lines.append("✅ **执行成功**")
            for port_name, port_val in result['output_values'].items():
                feedback_lines.append(f"**输出[{port_name}]**: `{_escape_for_display(port_val)}`")
        else:
            feedback_lines.append("✅ **执行成功**")

        if result.get("parameter_feedback"):
            feedback_lines.append(f"\n{result['parameter_feedback'].get('message', '')}")

        if result.get("newly_revealed"):
            _update_entities(sess, result["newly_revealed"])
            names = [e.get("id", "") for e in result["newly_revealed"]]
            feedback_lines.append(f"🎁 **新发现实体**: {', '.join(names)}")

        if result.get("investigate_hints"):
            for hint in result["investigate_hints"]:
                feedback_lines.append(
                    f"💡 **探索提示** (工具 `{hint.get('tool_id','')}`): {hint.get('hint','')}"
                )

    _add_log(sess, "feedback", "\n".join(feedback_lines))
    resp = make_response(jsonify({"ok": True}))
    _inject_cookie(resp, client_id)
    return resp


@app.route("/api/use_item", methods=["POST"])
def api_use_item():
    client_id = _get_client_id()
    sess = _get_session(client_id)
    if not sess["case_id"]:
        return jsonify({"ok": False, "error": "No case loaded"}), 400

    data = request.json or {}
    node_id = data.get("node_id", "").strip()
    arguments = data.get("arguments", {})
    if not node_id:
        return jsonify({"ok": False, "error": "node_id is required"}), 400

    args_display = ", ".join(f"{k}={repr(v)}" for k, v in arguments.items())
    _add_log(sess, "action", f"🧩 **use_item** `{node_id}`\n参数: {args_display}")

    try:
        resp_ev = requests.post(
            f"{SERVER_URL}/env/{sess['case_id']}/use_item",
            json={"node_id": node_id, "arguments": arguments},
            timeout=30,
        )
        resp_ev.raise_for_status()
        result = resp_ev.json()
    except Exception as e:
        _add_log(sess, "feedback", f"❌ 请求失败: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

    feedback_lines = []
    if not result.get("ok"):
        feedback_lines.append(f"❌ **失败**: {result.get('error', 'Unknown error')}")
    else:
        msg = result.get("message", "")
        if msg:
            feedback_lines.append(f"✅ {msg}")
        if result.get("narrative"):
            feedback_lines.append(f"**背景线索**: {result['narrative']}")
        if result.get("content"):
            content_val = result['content']
            if isinstance(content_val, (dict, list)):
                for k, v in (content_val.items() if isinstance(content_val, dict) else enumerate(content_val)):
                    feedback_lines.append(f"**内容[{k}]**: `{_escape_for_display(v)}`")
            else:
                feedback_lines.append(f"**内容**: `{_escape_for_display(content_val)}`")
        if result.get("newly_revealed"):
            _update_entities(sess, result["newly_revealed"])
            names = [e.get("id", "") for e in result["newly_revealed"]]
            feedback_lines.append(f"🎁 **新发现实体**: {', '.join(names)}")

    _add_log(sess, "feedback", "\n".join(feedback_lines))
    resp = make_response(jsonify({"ok": True}))
    _inject_cookie(resp, client_id)
    return resp


@app.route("/api/submit_answer", methods=["POST"])
def api_submit_answer():
    client_id = _get_client_id()
    sess = _get_session(client_id)
    if not sess["case_id"]:
        return jsonify({"ok": False, "error": "No case loaded"}), 400

    data = request.json or {}
    answer = data.get("answer", "")
    if not answer:
        return jsonify({"ok": False, "error": "answer is required"}), 400

    _add_log(sess, "action", f"🏆 **submit_answer**\n答案: `{answer}`")

    try:
        resp_ev = requests.post(
            f"{SERVER_URL}/env/{sess['case_id']}/submit_answer",
            json={"answer": answer},
            timeout=30,
        )
        resp_ev.raise_for_status()
        result = resp_ev.json()
    except Exception as e:
        _add_log(sess, "feedback", f"❌ 请求失败: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

    feedback_lines = []
    if result.get("is_win"):
        sess["win"] = True
        feedback_lines.append(f"🎉 **{result.get('victory_message', '恭喜！答案正确！')}**")
        _save_record(sess, success=True, gave_up=False)
    else:
        feedback_lines.append(f"❌ **答案不正确**: {result.get('error', '')}")

    _add_log(sess, "feedback", "\n".join(feedback_lines))
    resp = make_response(jsonify({"ok": True, "win": sess["win"]}))
    _inject_cookie(resp, client_id)
    return resp


@app.route("/api/list_cases")
def api_list_cases():
    """扫描 CASE_BASE_DIR，返回按难度分组的题目列表"""
    result = {}
    difficulty_dirs = ["5", "10", "15"]
    for diff in difficulty_dirs:
        narrative_dir = os.path.join(CASE_BASE_DIR, diff, "narrative")
        if not os.path.isdir(narrative_dir):
            result[diff] = []
            continue
        cases = []
        for fname in sorted(os.listdir(narrative_dir)):
            if fname.endswith(".json"):
                fpath = os.path.join(narrative_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    meta = data.get("metadata", {})
                    base_name = fname.replace("_narrative.json", "")
                    intro = meta.get("intro_narrative", "") or ""
                    short_intro = intro[:40].replace("\n", " ") + ("…" if len(intro) > 40 else "")
                    title = f"{base_name}  {short_intro}" if short_intro else base_name
                    win_node = meta.get("win_node_id", "") or data.get("win_node_id", "")
                    total_nodes = meta.get("total_nodes", diff)
                except Exception:
                    title = fname.replace("_narrative.json", "")
                    win_node = ""
                    total_nodes = diff
                cases.append({
                    "file_path": fpath,
                    "filename": fname,
                    "title": title,
                    "win_node": win_node,
                    "total_nodes": total_nodes,
                })
        result[diff] = cases
    return jsonify({"ok": True, "cases": result, "case_base_dir": CASE_BASE_DIR})


if __name__ == "__main__":
    import subprocess
    import socket

    def _get_local_ip():
        for iface in ("en0", "en1", "eth0"):
            try:
                out = subprocess.check_output(
                    ["ipconfig", "getifaddr", iface],
                    stderr=subprocess.DEVNULL, timeout=2
                ).decode().strip()
                if out and not out.startswith("127."):
                    return out
            except Exception:
                pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    local_ip = _get_local_ip()
    port = int(os.environ.get("PORT", 8419))
    print("=" * 55)
    print("Human Client 启动中（多用户模式）...")
    print(f"评测 Server : {SERVER_URL}")
    print(f"题目目录    : {CASE_BASE_DIR}")
    print(f"做题记录    : {RECORDS_CSV}")
    print(f"本机访问    : http://localhost:{port}")
    print(f"内网访问    : http://{local_ip}:{port}  ← 发给标注员")
    print("=" * 55)
    app.run(debug=False, host="0.0.0.0", port=port)
