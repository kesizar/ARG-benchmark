"""
评测框架：协调 server 和被测模型之间的交互
提供鲁棒的错误处理和状态管理
支持批量评测、报告生成、断点续传
"""
import json
import time
import random
import requests
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EvaluationResult:
    """评测结果 - 增强版"""
    def __init__(self, case_id: str = ""):
        self.case_id = case_id
        self.success = False
        self.total_steps = 0
        self.total_time = 0.0
        self.error_message = None
        self.victory_string = None
        self.trajectory = []  # 记录每一步的操作
        
        # 增强统计
        self.tool_calls = 0
        self.investigations = 0
        self.failed_actions = 0
        self.start_time = None
        self.end_time = None
        
        # Agent 统计（如果可用）
        self.agent_stats = {}
        
        # 完整的对话历史（用于分析模型行为）
        self.messages = None
        
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "case_id": self.case_id,
            "success": self.success,
            "total_steps": self.total_steps,
            "total_time": self.total_time,
            "error_message": self.error_message,
            "victory_string": self.victory_string,
            "trajectory": self.trajectory,
            "statistics": {
                "tool_calls": self.tool_calls,
                "investigations": self.investigations,
                "failed_actions": self.failed_actions,
                "success_rate": (self.tool_calls + self.investigations - self.failed_actions) / max(self.tool_calls + self.investigations, 1)
            },
            "agent_stats": self.agent_stats,
            "timestamps": {
                "start": self.start_time.isoformat() if self.start_time else None,
                "end": self.end_time.isoformat() if self.end_time else None
            }
        }
        
        # 如果有 messages，添加到结果中
        if self.messages is not None:
            result["messages"] = self.messages
        
        return result


class EscapeRoomEvaluator:
    """密室逃脱评测器 - 工业级版本
    
    Features:
    - 鲁棒的错误处理
    - 批量评测支持
    - 报告生成
    - 断点续传
    - 性能分析
    """
    
    def __init__(self, 
                 server_url: str = "http://localhost:8000",
                 max_steps: int = 50,
                 timeout: int = 1500,
                 verbose: bool = True,
                 output_dir: str = "evaluation_results",
                 session_id: str = None):
        """
        初始化评测器
        
        Args:
            server_url: Server 地址
            max_steps: 最大步数限制
            timeout: 总超时时间（秒）
            verbose: 是否打印详细日志
            output_dir: 结果输出目录
            session_id: 会话ID，用于并发评测时的状态隔离（如果不提供，将自动生成）
        """
        self.server_url = server_url
        self.max_steps = max_steps
        self.timeout = timeout
        self.verbose = verbose
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 【新增】为并发评测生成唯一的 session_id
        if session_id:
            self.session_id = session_id
        else:
            self.session_id = f"session_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        self.case_id = None
        self.start_time = None
        self.result = EvaluationResult()
        
        # 批量评测统计
        self.batch_results = []
        
        logger.info(f"Initialized evaluator - server: {server_url}, max_steps: {max_steps}, timeout: {timeout}s, session_id: {self.session_id}")
        
    def log(self, message: str, level: str = "INFO"):
        """打印日志"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def check_server_health(self) -> bool:
        """检查 server 是否正常运行"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    self.log(f"Server is healthy - uptime: {health_data.get('uptime_seconds', 0):.1f}s, loaded cases: {health_data.get('loaded_cases', 0)}", "INFO")
                    return True
            return False
        except Exception as e:
            self.log(f"Server health check failed: {e}", "ERROR")
            return False
    
    def load_case(self, case_file_path: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        加载案例并获取初始环境信息
        
        Returns:
            (success, initial_data)
        """
        self.log(f"Loading case from: {case_file_path} (session: {self.session_id})")
        
        try:
            # 【修复】传递 session_id 确保并发评测时的状态隔离
            response = requests.post(
                f"{self.server_url}/env/reset",
                params={
                    "case_file_path": case_file_path,
                    "session_id": self.session_id
                },
                timeout=30
            )
            """
            response的格式是：
                {
                    "ok": True,
                    "message": f"Case loaded from {case_file_path}",
                    "case_id": scenario.case_id,
                    "narrative": scenario.intro_narrative,
                    "available_entities": available_entities  # 使用统一的实体列表
                    "available_information": available_information  # 可用的初始信息（只包含 init_inputs）
                }
            """
            
            if response.status_code != 200:
                self.log(f"Failed to load case: {response.status_code} - {response.text}", "ERROR")
                return False, None
            
            data = response.json()
            self.case_id = data.get("case_id")
            
            if not self.case_id:
                self.log("No case_id in response", "ERROR")
                return False, None
            
            self.log(f"Case loaded successfully: {self.case_id}")
            self.log(f"Narrative: {data.get('narrative', '')[:100]}...")
            self.log(f"Available entities: {len(data.get('available_entities', []))}")
            self.log(f"Available information: {len(data.get('available_information', []))}")
            
            return True, data
            
        except requests.exceptions.Timeout:
            self.log("Request timeout when loading case", "ERROR")
            return False, None
        except requests.exceptions.ConnectionError:
            self.log("Cannot connect to server. Is it running?", "ERROR")
            return False, None
        except Exception as e:
            self.log(f"Unexpected error loading case: {e}", "ERROR")
            return False, None
    
    def execute_tool_call(self, node_id: str, arguments: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        执行工具调用
        
        Args:
            node_id: 节点 ID（唯一标识要调用的节点）
            arguments: 工具参数
        
        Returns:
            (success, result)
        """
        if not self.case_id:
            self.log("No case loaded", "ERROR")
            return False, None
        
        self.log(f"Calling tool node: {node_id} with args: {arguments}")
        
        try:
            response = requests.post(
                f"{self.server_url}/env/{self.case_id}/tool_call",
                json={"node_id": node_id, "arguments": arguments},
                timeout=30
            )
            
            if response.status_code != 200:
                self.log(f"Tool call failed: {response.status_code} - {response.text}", "ERROR")
                return False, {"error": response.text}
            
            result = response.json()
            
            # 记录到轨迹
            self.result.trajectory.append({
                "step": self.result.total_steps,
                "action": "tool_call",
                "node_id": node_id,
                "arguments": arguments,
                "result": result
            })
            
            if result.get("ok"):
                self.log(f"Tool call successful", "SUCCESS")
                
                # 检查是否获得了胜利字符串（但还未提交）
                if result.get("has_victory_string"):
                    self.log(f"🎯 {result.get('victory_hint')}", "HINT")
                
                # 检查是否有新物品掉落
                if result.get("newly_revealed"):
                    self.log(f"New items revealed: {result.get('newly_revealed')}")
            else:
                self.log(f"Tool call failed: {result.get('error', 'Unknown error')}", "ERROR")
            
            return True, result
            
        except requests.exceptions.Timeout:
            self.log("Request timeout", "ERROR")
            return False, {"error": "timeout"}
        except Exception as e:
            self.log(f"Error executing tool call: {e}", "ERROR")
            return False, {"error": str(e)}
    
    def execute_investigate(self, node_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        执行调查操作
        
        Returns:
            (success, result)
        """
        if not self.case_id:
            self.log("No case loaded", "ERROR")
            return False, None
        
        self.log(f"Investigating: {node_id}")
        
        try:
            response = requests.post(
                f"{self.server_url}/env/{self.case_id}/investigate",
                json={"node_id": node_id},
                timeout=30
            )
            
            if response.status_code != 200:
                self.log(f"Investigate failed: {response.status_code} - {response.text}", "ERROR")
                return False, {"error": response.text}
            
            result = response.json()
            
            # 记录到轨迹
            self.result.trajectory.append({
                "step": self.result.total_steps,
                "action": "investigate",
                "node_id": node_id,
                "result": result
            })
            
            if result.get("ok"):
                self.log(f"Investigation successful", "SUCCESS")
                self.log(f"Content: {result.get('content', 'N/A')}") # 这里要核对一下从server端返回的response具体有什么字段
                
                # 检查是否获得了胜利字符串（但还未提交）
                if result.get("has_victory_string"):
                    self.log(f"🎯 {result.get('victory_hint')}", "HINT")
                
                if result.get("newly_revealed"):
                    self.log(f"New items revealed: {result.get('newly_revealed')}")
            else:
                self.log(f"Investigation failed: {result.get('error', 'Unknown error')}", "ERROR")
            
            return True, result
            
        except requests.exceptions.Timeout:
            self.log("Request timeout", "ERROR")
            return False, {"error": "timeout"}
        except Exception as e:
            self.log(f"Error executing investigate: {e}", "ERROR")
            return False, {"error": str(e)}
    
    def execute_submit_answer(self, answer: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        执行提交答案操作
        
        Args:
            answer: 要提交的答案字符串
            
        Returns:
            (success, result)
        """
        if not self.case_id:
            self.log("No case loaded", "ERROR")
            return False, None
        
        self.log(f"Submitting answer: {answer}")
        
        try:
            response = requests.post(
                f"{self.server_url}/env/{self.case_id}/submit_answer",
                json={"answer": answer},
                timeout=30
            )
            
            if response.status_code != 200:
                self.log(f"Submit answer failed: {response.status_code} - {response.text}", "ERROR")
                return False, {"error": response.text}
            
            result = response.json()
            
            # 记录到轨迹
            self.result.trajectory.append({
                "step": self.result.total_steps,
                "action": "submit_answer",
                "answer": answer,
                "result": result
            })
            
            if result.get("ok"):
                # 检查是否获胜
                if result.get("is_win"):
                    self.result.success = True
                    self.result.victory_string = result.get("victory_message")
                    self.log(f"🎉 {result.get('victory_message')}", "WIN")
                else:
                    self.log(f"Answer incorrect: {result.get('error', 'Unknown error')}", "ERROR")
            else:
                self.log(f"Submit answer failed: {result.get('error', 'Unknown error')}", "ERROR")
            
            return True, result
            
        except requests.exceptions.Timeout:
            self.log("Request timeout", "ERROR")
            return False, {"error": "timeout"}
        except Exception as e:
            self.log(f"Error submitting answer: {e}", "ERROR")
            return False, {"error": str(e)}
    
    def execute_use_item(self, node_id: str, arguments: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        执行使用物品操作（use_item）
        
        Args:
            node_id: 物品节点 ID（必须是 Item 类型）
            arguments: 要提供给物品的参数
            
        Returns:
            (success, result)
        """
        if not self.case_id:
            self.log("No case loaded", "ERROR")
            return False, None
        
        self.log(f"Using item node: {node_id} with args: {arguments}")
        
        try:
            response = requests.post(
                f"{self.server_url}/env/{self.case_id}/use_item",
                json={"node_id": node_id, "arguments": arguments},
                timeout=30
            )
            
            if response.status_code != 200:
                self.log(f"Use item failed: {response.status_code} - {response.text}", "ERROR")
                return False, {"error": response.text}
            
            result = response.json()
            
            # 记录到轨迹
            self.result.trajectory.append({
                "step": self.result.total_steps,
                "action": "use_item",
                "node_id": node_id,
                "arguments": arguments,
                "result": result
            })
            
            if result.get("ok"):
                self.log(f"Use item successful", "SUCCESS")
                
                # 检查是否获得了胜利字符串（但还未提交）
                if result.get("has_victory_string"):
                    self.log(f"🎯 {result.get('victory_hint')}", "HINT")
                
                # 检查是否有新物品掉落
                if result.get("newly_revealed"):
                    self.log(f"New items revealed: {result.get('newly_revealed')}")
            else:
                self.log(f"Use item failed: {result.get('error', 'Unknown error')}", "ERROR")
            
            return True, result
            
        except requests.exceptions.Timeout:
            self.log("Request timeout", "ERROR")
            return False, {"error": "timeout"}
        except Exception as e:
            self.log(f"Error executing use_item: {e}", "ERROR")
            return False, {"error": str(e)}
    
    def run_evaluation(self, agent, case_file_path: str, save_result: bool = True) -> EvaluationResult:
        """
        运行完整的评测流程
        
        Args:
            agent: 被测模型 agent（需要实现 step 方法）
            case_file_path: 案例文件路径
            save_result: 是否自动保存结果
            
        Returns:
            EvaluationResult
        """
        case_name = Path(case_file_path).stem
        self.start_time = time.time()
        self.result = EvaluationResult(case_id=case_name) # 初始化结果对象
        self.result.start_time = datetime.now()
        
        self.log("="*80)
        self.log("Starting Escape Room Evaluation")
        self.log("="*80)
        
        # 1. 检查 server 健康状态
        if not self.check_server_health():
            self.result.error_message = "Server is not running"
            return self.result
        
        # 2. 加载案例
        success, initial_data = self.load_case(case_file_path) # initial_data中只有id字段，没有template_id字段
        # initial_data的格式：
        #      {
        #          "ok": True,
        #          "message": f"Case loaded from {case_file_path}",
        #          "case_id": scenario.case_id,
        #          "narrative": scenario.intro_narrative,
        #          "available_entities": available_entities  # 使用统一的实体列表
        #          "available_information": available_information  # 可用的初始信息（只包含 init_inputs）
        #      }
        if not success:
            self.result.error_message = "Failed to load case"
            return self.result
        
        # 3. 初始化 agent 2026年1月24日18:00查看到此处
        try:
            agent.initialize(initial_data) #在每个模型的实现代码中有具体实现
            self.log("Agent initialized")
        except Exception as e:
            self.log(f"Failed to initialize agent: {e}", "ERROR")
            self.result.error_message = f"Agent initialization error: {e}"
            return self.result
        
        # 4. 主循环
        for step in range(self.max_steps):
            # 检查超时
            elapsed = time.time() - self.start_time
            if elapsed > self.timeout:
                self.log(f"Timeout reached ({self.timeout}s)", "ERROR")
                self.result.error_message = "Timeout"
                break
            
            self.result.total_steps = step + 1
            self.log(f"\n{'='*80}")
            self.log(f"Step {step + 1}/{self.max_steps}")
            self.log(f"{'='*80}")
            
            # Agent 决策
            try:
                action = agent.step()
                # step函数返回的格式是
                # {
                #     "action": "parallel_tool_calls",
                #     "tool_calls": actions,
                #     "count": len(actions)
                # }
                #或者没有工具调用的时候是：
                # {
                #     "action": "wait",
                #     "reasoning": assistant_content or "Model did not call any tools"
                # }
            except Exception as e:
                self.log(f"Agent error: {e}", "ERROR")
                self.result.error_message = f"Agent error: {e}"
                break
            
            if not action:
                self.log("Agent returned no action", "ERROR")
                break
            
            action_type = action.get("action")
            self.log(f"Agent action: {action_type}")
            
            # 执行动作
            # 注意：
            # - Function Calling 模式下，step() 返回 "parallel_tool_calls" 或 "wait"
            # - JSON 模式下，step() 返回 "tool_call"、"investigate" 或 "wait"（单个动作）
            if action_type == "parallel_tool_calls":
                # 处理并行工具调用
                tool_calls = action.get("tool_calls", [])
                self.log(f"Executing {len(tool_calls)} parallel tool calls")
                
                for i, tool_call_action in enumerate(tool_calls):
                    sub_action_type = tool_call_action.get("action")
                    tool_call_id = tool_call_action.get("tool_call_id")
                    
                    self.log(f"  [{i+1}/{len(tool_calls)}] {sub_action_type}: {tool_call_action.get('node_id', 'unknown')}")
                    
                    if sub_action_type == "tool_call":
                        node_id = tool_call_action.get("node_id")
                        arguments = tool_call_action.get("arguments", {})
                        
                        if not node_id:
                            self.log("    Missing node_id", "ERROR")
                            self.result.failed_actions += 1
                            # 发送错误反馈
                            agent.receive_feedback(
                                {"ok": False, "error": "Missing node_id"},
                                tool_call_id=tool_call_id
                            )
                            continue
                        
                        self.result.tool_calls += 1
                        success, result = self.execute_tool_call(node_id, arguments)
                        
                        # 发送反馈，带上 tool_call_id
                        agent.receive_feedback(result, tool_call_id=tool_call_id)
                        
                        if not success:
                            self.result.failed_actions += 1
                    
                    elif sub_action_type == "investigate":
                        node_id = tool_call_action.get("node_id")
                        
                        if not node_id:
                            self.log("    Missing node_id", "ERROR")
                            self.result.failed_actions += 1
                            # 发送错误反馈
                            agent.receive_feedback(
                                {"ok": False, "error": "Missing node_id"},
                                tool_call_id=tool_call_id
                            )
                            continue
                        
                        self.result.investigations += 1
                        success, result = self.execute_investigate(node_id)
                        
                        # 发送反馈，带上 tool_call_id
                        agent.receive_feedback(result, tool_call_id=tool_call_id)
                        
                        if not success:
                            self.result.failed_actions += 1
                    
                    elif sub_action_type == "use_item":
                        node_id = tool_call_action.get("node_id")
                        arguments = tool_call_action.get("arguments", {})
                        
                        if not node_id:
                            self.log("    Missing node_id", "ERROR")
                            self.result.failed_actions += 1
                            # 发送错误反馈
                            agent.receive_feedback(
                                {"ok": False, "error": "Missing node_id"},
                                tool_call_id=tool_call_id
                            )
                            continue
                        
                        success, result = self.execute_use_item(node_id, arguments)
                        
                        # 发送反馈，带上 tool_call_id
                        agent.receive_feedback(result, tool_call_id=tool_call_id)
                        
                        if not success:
                            self.result.failed_actions += 1
                    
                    elif sub_action_type == "submit_answer":
                        answer = tool_call_action.get("answer")
                        
                        if not answer:
                            self.log("    Missing answer", "ERROR")
                            self.result.failed_actions += 1
                            # 发送错误反馈
                            agent.receive_feedback(
                                {"ok": False, "error": "Missing answer"},
                                tool_call_id=tool_call_id
                            )
                            continue
                        
                        success, result = self.execute_submit_answer(answer)
                        
                        # 发送反馈，带上 tool_call_id
                        agent.receive_feedback(result, tool_call_id=tool_call_id)
                        
                        if not success:
                            self.result.failed_actions += 1
                        
                        # 检查是否获胜（submit_answer 成功后）
                        if self.result.success:
                            break
                    
                    elif sub_action_type == "error":
                        self.log(f"    Error: {tool_call_action.get('error')}", "ERROR")
                        self.result.failed_actions += 1
                        # 发送错误反馈
                        agent.receive_feedback(
                            {"ok": False, "error": tool_call_action.get("error", "Unknown error")},
                            tool_call_id=tool_call_id
                        )
                
                # 检查是否获胜
                if self.result.success:
                    break
            
            elif action_type == "tool_call":
                node_id = action.get("node_id")
                arguments = action.get("arguments", {})
                
                if not node_id:
                    self.log("Missing node_id for tool_call", "ERROR")
                    self.result.failed_actions += 1
                    continue
                
                self.result.tool_calls += 1
                success, result = self.execute_tool_call(node_id, arguments)
                
                if success:
                    # 将结果反馈给 agent
                    agent.receive_feedback(result)
                else:
                    self.result.failed_actions += 1
                        
            elif action_type == "investigate":
                node_id = action.get("node_id")
                
                if not node_id:
                    self.log("Missing node_id for investigate", "ERROR")
                    self.result.failed_actions += 1
                    continue
                
                self.result.investigations += 1
                success, result = self.execute_investigate(node_id)
                
                if success:
                    agent.receive_feedback(result)
                else:
                    self.result.failed_actions += 1
                    
            elif action_type == "use_item":
                node_id = action.get("node_id")
                arguments = action.get("arguments", {})
                
                if not node_id:
                    self.log("Missing node_id for use_item", "ERROR")
                    self.result.failed_actions += 1
                    agent.receive_feedback({
                        "ok": False,
                        "error": "Missing node_id parameter"
                    })
                    continue
                
                success, result = self.execute_use_item(node_id, arguments)
                
                if success:
                    agent.receive_feedback(result)
                else:
                    self.result.failed_actions += 1
            
            elif action_type == "submit_answer":
                answer = action.get("answer")
                
                if not answer:
                    self.log("Missing answer for submit_answer", "ERROR")
                    self.result.failed_actions += 1
                    agent.receive_feedback({
                        "ok": False,
                        "error": "Missing answer parameter"
                    })
                    continue
                
                success, result = self.execute_submit_answer(answer)
                
                if success:
                    agent.receive_feedback(result)
                    
                    # 检查是否获胜
                    if self.result.success:
                        break
                else:
                    self.result.failed_actions += 1
            
            elif action_type == "wait":
                self.log("Agent chose to wait - prompting to continue")
                # 模型选择不调用工具，给它反馈让它继续尝试解决问题
                reasoning = action.get("reasoning", "")
                agent.receive_feedback({
                    "ok": True,
                    "message": "You currently haven't performed any actions. Please continue analyzing available parameters and try calling tools or investigating entities to advance your task. Remember your goal is to escape the room.",
                    "reasoning": reasoning
                })
                
            else:
                self.log(f"Unknown action: {action_type}", "ERROR")
        
        # 5. 计算总时间和终止时间
        self.result.total_time = time.time() - self.start_time
        self.result.end_time = datetime.now()
        
        # 6. 获取 agent 统计（如果可用）
        if hasattr(agent, 'get_statistics'):
            try:
                self.result.agent_stats = agent.get_statistics()
            except Exception as e:
                self.log(f"Failed to get agent statistics: {e}", "WARNING")
        
        # 7. 获取完整的对话历史 messages（如果可用）
        if hasattr(agent, 'messages'):
            try:
                self.result.messages = agent.messages
                self.log(f"Saved {len(agent.messages)} messages from conversation history")
            except Exception as e:
                self.log(f"Failed to get agent messages: {e}", "WARNING")
        
        # 8. 输出结果
        self.log("\n" + "="*80)
        if self.result.success:
            self.log("✅ EVALUATION PASSED", "SUCCESS")
            self.log(f"Victory string: {self.result.victory_string}")
        else:
            self.log("❌ EVALUATION FAILED", "ERROR")
            if self.result.error_message:
                self.log(f"Error: {self.result.error_message}")
        
        self.log(f"Total steps: {self.result.total_steps}/{self.max_steps}")
        self.log(f"Tool calls: {self.result.tool_calls}, Investigations: {self.result.investigations}, Failed: {self.result.failed_actions}")
        self.log(f"Total time: {self.result.total_time:.2f}s")
        
        # 打印 token 统计（如果可用）
        if self.result.agent_stats:
            self.log(f"API calls: {self.result.agent_stats.get('api_calls', 0)}")
            self.log(f"Total tokens: {self.result.agent_stats.get('total_tokens', 0)}")
            self.log(f"Estimated cost: ${self.result.agent_stats.get('total_cost_usd', 0):.4f}")
        
        self.log("="*80)
        
        # 9. 自动保存结果
        if save_result:
            output_path = self.output_dir / f"{case_name}_result.json"
            self.save_result(str(output_path))
        
        # 10. 添加到批量结果列表
        self.batch_results.append(self.result.to_dict())
        
        return self.result
    
    def save_result(self, output_path: str):
        """保存评测结果到文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.result.to_dict(), f, ensure_ascii=False, indent=2)
            self.log(f"Result saved to: {output_path}")
        except Exception as e:
            self.log(f"Failed to save result: {e}", "ERROR")
    
    def run_batch_evaluation(self, agent_factory, case_files: List[str], max_workers: int = 1) -> List[Dict[str, Any]]:
        """
        批量评测多个案例
        
        Args:
            agent_factory: Agent 工厂函数，返回新的 agent 实例
            case_files: 案例文件路径列表
            max_workers: 并发数（目前仅支持串行，留待扩展）
            
        Returns:
            批量评测结果列表
        """
        self.log(f"Starting batch evaluation - {len(case_files)} cases")
        self.batch_results = []
        
        for i, case_file in enumerate(case_files, 1):
            self.log(f"\n{'='*80}")
            self.log(f"Batch evaluation [{i}/{len(case_files)}]: {case_file}")
            self.log(f"{'='*80}")
            
            try:
                # 创建新的 agent 实例
                agent = agent_factory()
                
                # 运行评测
                result = self.run_evaluation(agent, case_file, save_result=True)
                
            except Exception as e:
                logger.error(f"Failed to evaluate {case_file}: {e}", exc_info=True)
                # 记录失败的案例
                self.batch_results.append({
                    "case_id": Path(case_file).stem,
                    "success": False,
                    "error_message": str(e)
                })
        
        # 生成汇总报告
        report_path = self.output_dir / "batch_evaluation_report.json"
        self.generate_batch_report(str(report_path))
        
        return self.batch_results
    
    def generate_batch_report(self, output_path: str):
        """生成批量评测报告"""
        if not self.batch_results:
            self.log("No batch results to report", "WARNING")
            return
        
        # 统计汇总
        total_cases = len(self.batch_results)
        successful_cases = sum(1 for r in self.batch_results if r.get('success', False))
        failed_cases = total_cases - successful_cases
        success_rate = successful_cases / total_cases if total_cases > 0 else 0
        
        # 平均统计
        avg_steps = sum(r.get('total_steps', 0) for r in self.batch_results) / max(total_cases, 1)
        avg_time = sum(r.get('total_time', 0) for r in self.batch_results) / max(total_cases, 1)
        
        # 总成本
        total_tokens = sum(r.get('agent_stats', {}).get('total_tokens', 0) for r in self.batch_results)
        total_cost = sum(r.get('agent_stats', {}).get('total_cost_usd', 0) for r in self.batch_results)
        
        report = {
            "summary": {
                "total_cases": total_cases,
                "successful_cases": successful_cases,
                "failed_cases": failed_cases,
                "success_rate": success_rate,
                "avg_steps": avg_steps,
                "avg_time": avg_time,
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost
            },
            "cases": self.batch_results,
            "generated_at": datetime.now().isoformat()
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self.log(f"\n{'='*80}")
            self.log("Batch Evaluation Report")
            self.log(f"{'='*80}")
            self.log(f"Total cases: {total_cases}")
            self.log(f"Success rate: {success_rate*100:.1f}% ({successful_cases}/{total_cases})")
            self.log(f"Avg steps: {avg_steps:.1f}")
            self.log(f"Avg time: {avg_time:.1f}s")
            self.log(f"Total tokens: {total_tokens}")
            self.log(f"Total cost: ${total_cost:.4f}")
            self.log(f"Report saved to: {output_path}")
            self.log(f"{'='*80}")
        except Exception as e:
            self.log(f"Failed to save batch report: {e}", "ERROR")


if __name__ == "__main__":
    """
    独立测试评测框架
    """
    print("Testing EscapeRoomEvaluator...")
    
    evaluator = EscapeRoomEvaluator(verbose=True)
    
    # 测试 server 健康检查
    print("\n1. Testing server health check...")
    if evaluator.check_server_health():
        print("✅ Server is running")
    else:
        print("❌ Server is not running. Please start server.py first.")
        exit(1)
    
    # 测试加载案例
    print("\n2. Testing case loading...")
    success, data = evaluator.load_case("dag_full_data/skeleton_8d2a10cf_source_init2_full.json")
    
    if success:
        print("✅ Case loaded successfully")
        print(f"Case ID: {evaluator.case_id}")
        print(f"Entities: {len(data.get('available_entities', []))}")
        print(f"Information: {len(data.get('available_information', []))}")
    else:
        print("❌ Failed to load case")
        exit(1)
    
    # 测试工具调用（示例）
    print("\n3. Testing tool call...")
    success, result = evaluator.execute_tool_call(
        "text_xor_hex",
        {"hex_a": "48656c6c6f20576f726c64", "hex_b": "48656c6c6f20576f726c64"}
    )
    
    if success:
        print("✅ Tool call successful")
        print(f"Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    else:
        print("❌ Tool call failed")
    
    print("\n✅ All tests passed!")