from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# 1. 细粒度接口类型定义
class InterfaceType(str, Enum):
    '''
    BIG_INT
    TEXT_GENERIC
    HEX_STRING
    FILE_ID
    HEX_STRING_KEY_AES
    HEX_STRING_IV_AES
    CODE_PYTHON
    HIDDEN_ITEM
    ITEM
    '''
    # --- 基础类型 ---
    TEXT_GENERIC = "Text_Generic"
    BIG_INT = "Big_Int"

    # --- 编码/格式化字符串 ---
    HEX_STRING = "Hex_String" # 通用 Hex

    # --- 特定用途的 Hex 字符串 (用于精确匹配) ---
    HEX_STRING_KEY_AES = "Hex_String_Key_AES"
    HEX_STRING_IV_AES = "Hex_String_IV_AES"

    # --- 文件类型 ---
    FILE_ID = "File_Id"

    # --- 代码/脚本 ---
    CODE_PYTHON = "Code_Python"

    # --- 实体交互类型 (严格命名) ---
    ITEM = "Item"              # 主动掉落接口 (Tool -> Item)
    HIDDEN_ITEM = "Hidden_Item" # 被动掉落接口 (Item -> Item)

# 3. 端口定义
class Port(BaseModel):
    name: str
    type: InterfaceType
    description: str

# 4. 统一节点定义 (融合工具和物品)
class Node(BaseModel):
    id: str
    name: str
    description: str
    type: str  # "Tool" or "Item"

    # 接口定义
    inputs: List[Port] = []
    outputs: List[Port] = []

    # 状态字段
    content: Optional[Any] = None        # 物品有内容，工具为None
    if_success: Optional[bool] = None    # 工具初始为False，物品为None
    initial_visible: bool = False

    # 运行时状态 (Server维护)
    is_revealed: bool = False
    
    # 标记该 Tool 节点是否有待触发的 HIDDEN_ITEM 掉落
    # 当 Tool 按照 golden_input 正确执行且有 HIDDEN_ITEM 输出边时设为 True
    # 在 investigate 该 Tool 时触发掉落并重置为 False
    has_hidden_item_ready: bool = False
    
    # 初始输入值 (metadata.initial_values.init_inputs，用于渐进式暴露判断)
    init_input_values: Dict[str, Any] = {}
    
    # Golden 输入值 (nodes[].inputs[].value，用于评测验证)
    golden_input_values: Dict[str, Any] = {}
    
    # Golden 输出值 (nodes[].outputs[].value，用于评测验证和 Item 节点的 content)
    golden_output_values: Dict[str, Any] = {}
    
    # 实际获得的输出值历史 (工具每次执行后实际返回的输出列表，用于渐进式暴露判断)
    # 格式: List[Dict[str, Any]]，每个元素是一次执行的输出字典
    actual_outputs_history: List[Dict[str, Any]] = []
    
    # 逻辑规则 (用于终端机等复杂物品)
    logic_rules: Optional[Dict[str, Any]] = None

    def copy(self, **kwargs):
        """Helper to create a copy with updated fields."""
        data = self.dict()
        data.update(kwargs)
        return Node(**data)

# 5. 边定义 (拓扑结构)
class Edge(BaseModel):
    source_id: str
    target_id: str
    connection_type: InterfaceType # 直接使用 InterfaceType
    # 如果是 Data_Flow，指定端口对应关系
    source_port: Optional[str] = None
    target_port: Optional[str] = None

# 6. 完整图定义
class GraphScenario(BaseModel):
    case_id: str
    title: str
    intro_narrative: str
    nodes: Dict[str, Node]
    edges: List[Edge]
    difficulty: int
    win_node_id: str # 标记哪个节点是最终目标（通常是一个提交工具或最终物品）
