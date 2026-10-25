"""
Step 1: DAG Skeleton Generator
This module generates only the DAG skeleton (nodes and edges) without content filling.
The skeleton is saved as JSON for quality checking and further processing.
"""

import random
import uuid
import json
import os
import argparse
from typing import List, Dict, Tuple
from models import Node, Edge, Port, InterfaceType
from assets import TOOL_TEMPLATES, ITEM_TEMPLATES, CONTAINER_TEMPLATES, TERMINAL_TEMPLATES, DROPPABLE_TOOL_TEMPLATES

# ================== 特殊输入端口配置 ==================

# 一旦某个输出端口喂给这些输入端口，该输出端口之后不能再作为任何其他边的 source
SPECIAL_SINGLE_USE_INPUT_PORTS = {
    ("regex_search", "pattern"),
    ("json_get", "jsonpath"),
    ("csv_query", "where"),
    ("time_convert", "iso"),
    ("otp_totp_generate", "base32_secret"),
    ("base64_decode", "data"),
}


class DAGSkeletonGenerator:
    """Generates DAG skeleton (structure only, no content)."""

    def __init__(self, droppable_ratio: float = 0.3):
        """
        Initialize DAG skeleton generator.
        
        Args:
            droppable_ratio: Probability of using droppable tool templates (with ITEM/HIDDEN_ITEM triggers)
                           Range: 0.0 to 1.0 (default: 0.3 = 30%)
        """
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.node_counter = 0
        self.template_usage: Dict[str, str] = {}  # Track which template each node uses
        self.final_goal_node: Node = None  # Store reference to the final goal node
        self.distractor_type: str = "none"  # 干扰项类型: "none", "A", "B", "both"
        self.droppable_ratio: float = max(0.0, min(1.0, droppable_ratio))  # Clamp to [0, 1]

        # 新增：记录"已经被用于特殊输入端口"的输出端口 (source_node_id, source_port_name)
        self.special_consumed_ports: set[tuple[str, str]] = set()
        
        # 新增：记录每个目标节点已经使用的源端口，避免同一个节点的不同输入使用同一个源端口
        # key: target_node_id, value: set of (source_node_id, source_port_name) tuples
        self.target_used_sources: Dict[str, set[tuple[str, str]]] = {}

    def _get_tool_template_pool(self) -> List[Dict]:
        """
        Get the tool template pool based on droppable_ratio.
        Combines original tools/terminals with droppable variants according to the ratio.
        
        Returns:
            List of tool templates to use for DAG generation
        """
        if self.droppable_ratio <= 0:
            # No droppable tools, only use originals
            return TOOL_TEMPLATES + TERMINAL_TEMPLATES
        elif self.droppable_ratio >= 1:
            # Only droppable tools
            return DROPPABLE_TOOL_TEMPLATES
        else:
            # Mix both according to ratio
            # If droppable_ratio = 0.3, then 30% chance to use droppable pool
            if random.random() < self.droppable_ratio:
                return DROPPABLE_TOOL_TEMPLATES
            else:
                return TOOL_TEMPLATES + TERMINAL_TEMPLATES
    
    def _create_node_from_template(self, template: Dict, node_type: str) -> Node:
        """Create a node from a template."""
        self.node_counter += 1
        unique_id = template["id_template"].format(i=self.node_counter)
        if unique_id in self.nodes:
            unique_id = f"{unique_id}_{uuid.uuid4().hex[:4]}"

        # Track template usage
        self.template_usage[unique_id] = template["id_template"]

        return Node(
            id=unique_id,
            name=template["name"],
            description=template["description"],
            type=node_type,
            inputs=template.get("inputs", []),
            outputs=template.get("outputs", []),
            logic_rules=template.get("logic_rules", None)
        )

    # def _is_output_port_reusable(self, node_id: str, port_name: str, port_type: InterfaceType) -> bool:
    #     """
    #     Check if an output port can be reused.

    #     物理对象类型（ITEM, HIDDEN_ITEM）只能被使用一次（不能多次使用）
    #     基本数据类型（STRING, INT, BIG_INT, HEX_STRING等）可以被多次使用
    #     """
    #     # 物理对象类型：只能被使用一次
    #     object_types = [InterfaceType.ITEM, InterfaceType.HIDDEN_ITEM]

    #     if port_type in object_types:
    #         # 检查这个端口是否已经被使用过
    #         for edge in self.edges:
    #             if edge.source_id == node_id and edge.source_port == port_name:
    #                 return False  # 已经被使用过，不能再用
    #         return True  # 未被使用，可以使用
    #     else:
    #         # 基本数据类型：可以被多次使用
    #         return True
    def _is_output_port_reusable(self, node_id: str, port_name: str, port_type: InterfaceType) -> bool:
        """
        Check if an output port can be reused.

        1. 如果该输出端口已经被用来喂给“特殊输入端口”，则不能再被使用；
        2. 物理对象类型（ITEM, HIDDEN_ITEM）本身语义仍然是一次性（和之前一致）；
        3. 其他普通类型（数字、普通字符串等）可以被多次复用。
        """

        # 1) 已经被特殊输入端口消费过：永远不能再用
        if (node_id, port_name) in self.special_consumed_ports:
            return False

        # 2) 物理对象类型：只能被使用一次（沿用原来的逻辑）
        object_types = [InterfaceType.ITEM, InterfaceType.HIDDEN_ITEM]

        if port_type in object_types:
            for edge in self.edges:
                if edge.source_id == node_id and edge.source_port == port_name:
                    return False  # 已经被使用过，不能再用
            return True  # 未被使用，可以使用

        # 3) 其他类型：可以多次复用
        return True


    def _find_reusable_nodes(self, req_type: InterfaceType) -> List[Node]:
        """Find existing nodes that output the required type and can be reused."""
        candidates = []
        for node in self.nodes.values():
            for port in node.outputs:          
                if port.type == req_type and self._is_output_port_reusable(node.id, port.name, req_type):
                    candidates.append(node)
                    break
        return candidates

    # def _connect_nodes(self, source: Node, target: Node, req_type: InterfaceType,
    #                   source_port_name: str, target_port_name: str):
    #     """Create an edge between two nodes."""
    #     self.edges.append(Edge(
    #         source_id=source.id,
    #         target_id=target.id,
    #         connection_type=req_type,
    #         source_port=source_port_name,
    #         target_port=target_port_name
    #     ))
    def _connect_nodes(self, source: Node, target: Node, req_type: InterfaceType,
                      source_port_name: str, target_port_name: str):
        """Create an edge between two nodes."""
        self.edges.append(Edge(
            source_id=source.id,
            target_id=target.id,
            connection_type=req_type,
            source_port=source_port_name,
            target_port=target_port_name
        ))

        # 新增：如果 target 的这个输入端口属于"特殊输入端口"集合，
        # 则将 source 的这个输出端口标记为已被特殊消费，之后不再允许复用
        target_template_id = self.template_usage.get(target.id)
        if target_template_id is not None and (target_template_id, target_port_name) in SPECIAL_SINGLE_USE_INPUT_PORTS:
            self.special_consumed_ports.add((source.id, source_port_name))
        
        # 新增：记录这个目标节点使用了哪个源端口，防止同一个节点的不同输入使用同一个源端口
        if target.id not in self.target_used_sources:
            self.target_used_sources[target.id] = set()
        self.target_used_sources[target.id].add((source.id, source_port_name))


    def _has_path(self, start_node_id: str, end_node_id: str) -> bool:
        """Check if there is a path from start_node to end_node using BFS."""
        if start_node_id == end_node_id:
            return True

        queue = [start_node_id]
        visited = {start_node_id}

        while queue:
            curr = queue.pop(0)
            if curr == end_node_id:
                return True

            for edge in self.edges:
                if edge.source_id == curr:
                    if edge.target_id not in visited:
                        visited.add(edge.target_id)
                        queue.append(edge.target_id)
        return False

    def _select_random_final_goal(self) -> Tuple[Node, List[Tuple[str, InterfaceType]]]:
        """
        随机选择一个有输入需求的模板作为最终节点。
        返回: (final_goal_node, [(input_port_name, input_port_type), ...])
        """
        # 收集所有有输入的模板
        templates_with_inputs = []

        # 从所有模板类型中收集有输入的模板
        for tmpl in TOOL_TEMPLATES + TERMINAL_TEMPLATES + ITEM_TEMPLATES + CONTAINER_TEMPLATES:
            if tmpl.get("inputs", []):
                templates_with_inputs.append((tmpl, "Tool" if tmpl in TOOL_TEMPLATES or tmpl in TERMINAL_TEMPLATES else "Item"))

        if not templates_with_inputs:
            # 如果没有有输入的模板，使用默认的 final_goal
            final_goal = Node(
                id="final_goal_code",
                name="Final Escape Code",
                description="The code needed to unlock the door.",
                type="Item",
                inputs=[
                    Port(name="code", type=InterfaceType.STRING, description="The flag")
                ],
                outputs=[]
            )
            return final_goal, [("code", InterfaceType.STRING)]

        # 随机选择一个模板
        tmpl, node_type = random.choice(templates_with_inputs)

        # 创建最终节点
        final_goal = self._create_node_from_template(tmpl, node_type)  # node_type是Tool或Item，final_goal是节点

        # 获取所有输入端口
        input_ports = [(port.name, port.type) for port in final_goal.inputs]

        return final_goal, input_ports

    def _generate_main_graph(self, target_difficulty: int, final_goal: Node, input_ports: List[Tuple[str, InterfaceType]]):
        """Generate the main puzzle graph (reverse growth)."""
        # 将所有输入端口加入 pending_inputs
        # pending_inputs中存储的是：(node_id, port_name, port_type, retry_count)
        pending_inputs: List[Tuple[str, str, InterfaceType, int]] = [
            (final_goal.id, port_name, port_type, 0) for port_name, port_type in input_ports
        ]

        while len(self.nodes) < target_difficulty:
            # 如果 pending_inputs 为空，停止生成
            # 注意：虽然我们无条件地将新节点的所有输入端口加入 pending_inputs，
            # 但 pending_inputs 仍然可能变空。这可能发生在以下情况：
            # 1. 所有输入端口都被处理完了，但还没有达到目标节点数
            # 2. 某些输入类型无法被任何模板的输出类型满足（已通过修改 assets.py 解决）
            #
            # 在修改 assets.py 后，所有输入类型都可以被满足：
            # - Base32_Secret → STRING
            # - Code_Python → STRING
            # - File_Path_Graph_Json → STRING
            # - Hex_String_Hash_SHA256 → HEX_STRING
            # - Json_Path → STRING
            # - Lat_Lon → STRING
            # - Sql_Where → STRING
            if not pending_inputs:
                break

            target_idx = random.randrange(len(pending_inputs))
            target_node_id, target_port_name, req_type, retry_count = pending_inputs.pop(target_idx)
            target_node = self.nodes[target_node_id]

            # 如果重试次数过多，跳过这个输入端口
            if retry_count > 5:
                continue

            # 1. Try to reuse existing nodes (Graph structure)
            reusable_candidates = self._find_reusable_nodes(req_type)
            # 提高复用概率：从 0.2-0.6 提升到 0.5-0.8
            reuse_prob = 0.3 + 0.3 * (len(self.nodes) / target_difficulty) # 我把0.5改成了0.3
            # reuse_prob = 0.2
            # Filter candidates to prevent cycles and ensure available ports
            used_sources = self.target_used_sources.get(target_node.id, set())
            valid_candidates = []
            for cand in reusable_candidates:
                if cand.id != target_node.id and not self._has_path(target_node.id, cand.id):
                    # 检查该候选节点是否有可用的输出端口（未被当前目标节点使用过）
                    has_available_port = any(
                        (cand.id, p.name) not in used_sources 
                        for p in cand.outputs if p.type == req_type
                    )
                    if has_available_port:
                        valid_candidates.append(cand)

            if valid_candidates and random.random() < reuse_prob: #有可以使用的节点并且按照概率复用
                source_node = random.choice(valid_candidates)
                
                # 获取该目标节点已使用的源端口
                used_sources = self.target_used_sources.get(target_node.id, set())
                
                # 找到所有可用的输出端口（类型匹配且未被该目标节点使用过）
                available_ports = [
                    p.name for p in source_node.outputs 
                    if p.type == req_type and (source_node.id, p.name) not in used_sources
                ]
                
                # 如果有可用端口，选择一个；否则重新将此输入加入待处理队列
                if available_ports:
                    source_port_name = random.choice(available_ports)
                    self._connect_nodes(source_node, target_node, req_type, source_port_name, target_port_name)
                    continue
                else:
                    # 当前选中的源节点的所有匹配端口都已被此目标节点使用过，重新加入队列
                    pending_inputs.append((target_node_id, target_port_name, req_type, retry_count + 1))
                    continue

            # 2. Create new node (Tree structure)
            candidates = []
            # A. Tools (including droppable variants based on ratio)
            tool_pool = self._get_tool_template_pool()
            for tmpl in tool_pool:
                for out_port in tmpl.get("outputs", []):
                    if out_port.type == req_type:
                        candidates.append((tmpl, "Tool", out_port.name))
            # B. Containers (for HIDDEN_ITEM outputs)
            for tmpl in CONTAINER_TEMPLATES:
                for out_port in tmpl.get("outputs", []):
                    if out_port.type == req_type:
                        candidates.append((tmpl, "Item", out_port.name))
            # C. Items
            if len(self.nodes) > target_difficulty * 0.8 or not candidates:
                for tmpl in ITEM_TEMPLATES:
                    for out_port in tmpl.get("outputs", []):
                        if out_port.type == req_type:
                            candidates.append((tmpl, "Item", out_port.name))

            if not candidates:
                # 如果找不到匹配的候选节点，将这个输入端口重新加入 pending_inputs
                # 增加重试计数，防止无限循环
                pending_inputs.append((target_node_id, target_port_name, req_type, retry_count + 1))
                continue

            tmpl, node_type, source_port_name = random.choice(candidates)
            new_node = self._create_node_from_template(tmpl, node_type)
            self.nodes[new_node.id] = new_node

            self._connect_nodes(new_node, target_node, req_type, source_port_name, target_port_name)

            # Add inputs of the new node to pending queue
            for port in new_node.inputs:
                pending_inputs.append((new_node.id, port.name, port.type, 0))


    def _generate_distractors_type_a(self, count: int):
        """
        生成 A 类干扰项：独立于 DAG 的干扰项
        包括：孤立项、容器链、工具链（都不连接到主 DAG）

        确保每次迭代都生成一个干扰项
        """
        if count <= 0:
            return

        for _ in range(count):
            distractor_subtype = random.random()

            if distractor_subtype < 0.4:
                # Type A1: Isolated Item (Dead End) - 40%
                tmpl = random.choice(ITEM_TEMPLATES)
                node = self._create_node_from_template(tmpl, "Item")
                node.initial_visible = True
                self.nodes[node.id] = node

            elif distractor_subtype < 0.7:
                # Type A2: Fake Chain (Container -> Item) - 30%
                # 创建一个容器，然后根据容器的输出类型选择兼容的内容模板
                container_tmpl = random.choice(CONTAINER_TEMPLATES)
                container = self._create_node_from_template(container_tmpl, "Item")
                container.initial_visible = True
                self.nodes[container.id] = container

                # 找到容器的输出端口
                container_outputs = container.outputs
                created_chain = False

                if container_outputs:
                    # 随机选择一个输出端口
                    container_out_port = random.choice(container_outputs)
                    container_out_type = container_out_port.type
                    container_out_name = container_out_port.name

                    # 找一个输入类型匹配的内容模板
                    matching_contents = []
                    for tmpl in ITEM_TEMPLATES:
                        for in_port in tmpl.get("inputs", []):
                            if in_port.type == container_out_type:
                                matching_contents.append((tmpl, in_port.name))

                    if matching_contents:
                        content_tmpl, content_in_name = random.choice(matching_contents)
                        content = self._create_node_from_template(content_tmpl, "Item")
                        content.content = "Nothing useful here."
                        content.initial_visible = True
                        self.nodes[content.id] = content

                        # 连接容器到内容
                        self._connect_nodes(container, content, container_out_type, container_out_name, content_in_name)
                        created_chain = True

                # 如果容器链创建失败，至少保留容器作为孤立项
                # (容器已经被添加到 self.nodes 中)

            else:
                # Type A3: Isolated Tool - 30%
                # 创建一个独立的工具，不连接到任何地方
                tool_pool = self._get_tool_template_pool()
                tool_tmpl = random.choice(tool_pool)
                tool = self._create_node_from_template(tool_tmpl, "Tool")
                tool.initial_visible = True
                self.nodes[tool.id] = tool

    def _generate_distractors_type_b(self, count: int):
        """
        生成 B 类干扰项：和主 DAG 相连，但输出或内容后续没有用的干扰项
        这些节点接收主 DAG 中某个节点的输出，但该输出后续没有被使用（死胡同）

        结构：主 DAG 节点 → 干扰项节点（无后续）

        关键：干扰项的所有输入端口都要被连接到 DAG 中的节点，确保干扰项是可以被利用的，
        只是它的输出没有被使用。

        确保每次迭代都生成一个干扰项
        """
        if count <= 0:
            return

        for _ in range(count):
            # 从主 DAG 中随机选择一个有输出的节点作为源
            if not self.nodes:
                continue

            # 找到所有有输出的节点
            source_candidates = [n for n in self.nodes.values() if n.outputs and n != self.final_goal_node]
            if not source_candidates:
                continue

            # 尝试不同的源节点，直到成功创建干扰项
            created_distractor = False
            attempted_sources = set()

            while not created_distractor and len(attempted_sources) < len(source_candidates):
                source_node = random.choice(source_candidates)

                # 避免重复尝试同一个源节点
                if source_node.id in attempted_sources:
                    continue
                attempted_sources.add(source_node.id)

                # 只在当前允许复用的输出端口中选择，避免使用已被特殊输入占用的端口
                usable_outputs = [
                    p for p in source_node.outputs
                    if self._is_output_port_reusable(source_node.id, p.name, p.type)
                ]
                if not usable_outputs:
                    continue

                # 随机选择源节点的一个输出端口
                # source_output = random.choice(source_node.outputs)
                source_output = random.choice(usable_outputs)
                source_output_type = source_output.type
                source_output_name = source_output.name

                # 找出所有能和该源节点的输出连接的模板
                # 包括：工具、项目等
                matching_templates = []

                # 从工具中找（包括可掉落工具）
                tool_pool = self._get_tool_template_pool()
                for tmpl in tool_pool:
                    for in_port in tmpl.get("inputs", []):
                        if in_port.type == source_output_type:
                            matching_templates.append((tmpl, "Tool", in_port.name))

                # 从项目中找
                for tmpl in ITEM_TEMPLATES:
                    for in_port in tmpl.get("inputs", []):
                        if in_port.type == source_output_type:
                            matching_templates.append((tmpl, "Item", in_port.name))

                if matching_templates:
                    # 随机选择一个匹配的模板
                    tmpl, node_type, input_port_name = random.choice(matching_templates)
                    distractor_node = self._create_node_from_template(tmpl, node_type)
                    distractor_node.initial_visible = True
                    self.nodes[distractor_node.id] = distractor_node

                    # 连接源节点的输出到干扰项的这个输入端口
                    self._connect_nodes(source_node, distractor_node, source_output_type, source_output_name, input_port_name)

                    # 关键：填充干扰项的其他输入端口
                    # 确保干扰项的所有输入都被连接，这样它才是可以被利用的
                    for port in distractor_node.inputs:
                        # 跳过已经连接的端口
                        if port.name == input_port_name:
                            continue

                        # 为这个输入端口找一个源节点
                        port_type = port.type

                        # 首先尝试从现有节点中复用
                        reusable_candidates = self._find_reusable_nodes(port_type)
                        valid_candidates = []
                        for cand in reusable_candidates:
                            if cand.id != distractor_node.id and not self._has_path(distractor_node.id, cand.id) and cand != self.final_goal_node:
                                valid_candidates.append(cand)

                        used_existing = False # 标记本端口是否已经成功复用现有节点
                        if valid_candidates:
                            # 复用现有节点
                            # source = random.choice(valid_candidates)
                            # source_port_name = next(p.name for p in source.outputs if p.type == port_type)
                            # self._connect_nodes(source, distractor_node, port_type, source_port_name, port.name)
                            source = random.choice(valid_candidates)
                            # 修改点：只从当前“仍可复用”的输出端口中挑选
                            candidate_ports = [
                                p for p in source.outputs 
                                if p.type == port_type
                                and self._is_output_port_reusable(source.id, p.name, port_type)
                            ]
                            # if not candidate_ports:
                            #     continue
                            # source_port_name = random.choice(candidate_ports).name
                            # self._connect_nodes(source, distractor_node, port_type, source_port_name, port.name)
                            if candidate_ports:
                                source_port = random.choice(candidate_ports)
                                source_port_name = source_port.name
                                self._connect_nodes(source, distractor_node, port_type, source_port_name, port.name)
                                used_existing = True
                        
                        # if not used_existing:
                        #     # 如果无法复用现有节点（包括 candidate_ports 为空的情况），
                        #     # 则创建新的源节点来填充这个输入
                        # # else:
                        # #     # 创建新的源节点来填充这个输入
                        # #     # 从项目模板中选择能输出这个类型的模板
                        #     matching_sources = []
                        #     for tmpl in ITEM_TEMPLATES:
                        #         for out_port in tmpl.get("outputs", []):
                        #             if out_port.type == port_type:
                        #                 matching_sources.append((tmpl, out_port.name))

                        #     if matching_sources:
                        #         source_tmpl, source_port_name = random.choice(matching_sources)
                        #         source_node_new = self._create_node_from_template(source_tmpl, "Item")
                        #         self.nodes[source_node_new.id] = source_node_new
                        #         self._connect_nodes(source_node_new, distractor_node, port_type, source_port_name, port.name)

                    created_distractor = True

    def _generate_distractors(self, count: int, distractor_type: str = "both"):
        """
        生成干扰项
        distractor_type: "none" (无干扰项), "A" (只有A类), "B" (只有B类), "both" (两种都有)
        """
        if count <= 0 or distractor_type == "none":
            return

        if distractor_type == "A":
            self._generate_distractors_type_a(count)
        elif distractor_type == "B":
            self._generate_distractors_type_b(count)
        elif distractor_type == "both":
            # 平均分配 A 类和 B 类干扰项
            count_a = count // 2
            count_b = count - count_a
            self._generate_distractors_type_a(count_a)
            self._generate_distractors_type_b(count_b)

    def generate_skeleton(self, difficulty: int, distractor_type: str = "both", distractor_ratio: float = 0.25) -> Dict:
        """
        Generate DAG skeleton and return as dictionary.

        Args:
            difficulty: Target number of nodes
            distractor_type: Type of distractors to generate
                - "none": No distractors
                - "A": Only type A distractors (isolated from main DAG)
                - "B": Only type B distractors (connected to main DAG but unused)
                - "both": Both type A and B distractors (default)
            distractor_ratio: Ratio of distractors to main DAG nodes (default 0.3 = 30%)
                - If distractor_type is "none", this is ignored
                - If distractor_type is not "none", at least 1 distractor will be generated
        """
        self.nodes = {}
        self.edges = []
        self.node_counter = 0
        self.template_usage = {}
        self.final_goal_node = None  # Reset final goal node reference
        self.distractor_type = distractor_type  # Save distractor type

        # 新增：每次生成新的 skeleton 时清空
        self.special_consumed_ports = set()

        # 1. Create Final Goal (随机选择一个有输入需求的模板)
        final_goal, input_ports = self._select_random_final_goal()  # final_goal是节点名字、input_ports是输入端口
        self.nodes[final_goal.id] = final_goal
        self.final_goal_node = final_goal  # Save reference to final goal node

        # 2. Generate Main Graph
        # main_difficulty = max(1, int(difficulty * 0.8))
        main_difficulty = int(difficulty)
        self._generate_main_graph(main_difficulty, final_goal, input_ports)

        # Ensure Terminal
        # has_terminal = any("terminal" in node.id.lower() for node in self.nodes.values())
        # if not has_terminal:
        #     terminal_tmpl = random.choice(TERMINAL_TEMPLATES)
        #     new_terminal = self._create_node_from_template(terminal_tmpl, "Tool")
        #     self.nodes[new_terminal.id] = new_terminal
        #     if new_terminal.outputs:
        #         terminal_out_port = random.choice(new_terminal.outputs)
        #         compatible_nodes = []
        #         for node_id, node in self.nodes.items():
        #             if node_id != new_terminal.id:
        #                 for node_in_port in node.inputs:
        #                     if node_in_port.type == terminal_out_port.type:
        #                         compatible_nodes.append((node, node_in_port.name))
        #         if compatible_nodes:
        #             target_node, target_port = random.choice(compatible_nodes)
        #             self._connect_nodes(new_terminal, target_node, terminal_out_port.type, terminal_out_port.name, target_port)

        # 3. Generate Distractors (干扰项)
        if distractor_type != "none":
            # 干扰项数量 = 当前节点数 * 比例，至少生成 1 个干扰项
            # distractor_count = max(1, int(len(self.nodes) * distractor_ratio))
            distractor_count = 1
            self._generate_distractors(distractor_count, distractor_type)

        # 4. Set Initial Visibility
        nodes_with_incoming_drop_edges = set()
        for edge in self.edges:
            if edge.connection_type in [InterfaceType.ITEM, InterfaceType.HIDDEN_ITEM]:
                nodes_with_incoming_drop_edges.add(edge.target_id)

        for node_id, node in self.nodes.items():
            if node_id not in nodes_with_incoming_drop_edges:
                node.initial_visible = True
                node.is_revealed = True

        # Convert to dictionary for JSON serialization
        return self._to_dict()

    def _to_dict(self) -> Dict:
        """Convert skeleton to dictionary format."""
        nodes_list = []
        for node_id, node in self.nodes.items():
            node_dict = {
                "id": node.id,
                "name": node.name,
                "description": node.description,
                "type": node.type,
                "template_id": self.template_usage.get(node.id, "unknown"),
                "initial_visible": node.initial_visible,
                "is_revealed": node.is_revealed,
                "inputs": [
                    {
                        "name": port.name,
                        "type": port.type.value,
                        "description": port.description
                    }
                    for port in node.inputs
                ],
                "outputs": [
                    {
                        "name": port.name,
                        "type": port.type.value,
                        "description": port.description
                    }
                    for port in node.outputs
                ]
            }
            nodes_list.append(node_dict)

        edges_list = []
        for edge in self.edges:
            edge_dict = {
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "connection_type": edge.connection_type.value,
                "source_port": edge.source_port,
                "target_port": edge.target_port
            }
            edges_list.append(edge_dict)

        # 使用保存的 final_goal_node 作为 win_node
        # final_goal_node 是逆向生成 DAG 时的最终节点，它的输出就是整个密室问题成功与否的判断标志
        win_node = self.final_goal_node
        win_node_id = win_node.id if win_node else None

        # 确定成功条件
        win_condition = None
        if win_node:
            if win_node.type == "Tool":
                # 如果是工具，成功条件是工具的输出结果
                if win_node.outputs:
                    output_port = win_node.outputs[0]
                    win_condition = {
                        "type": "tool_output",
                        "node_id": win_node_id,
                        "output_port": output_port.name,
                        "output_type": output_port.type.value,
                        "description": f"Execute {win_node.name} and get the output from port '{output_port.name}'"
                    }
            else:  # Item 或其他类型
                # 如果是项目，成功条件是项目的内容
                win_condition = {
                    "type": "item_content",
                    "node_id": win_node_id,
                    "description": f"Obtain the content of {win_node.name}"
                }

        return {
            "metadata": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "win_node_id": win_node_id,
                "win_condition": win_condition
            },
            "nodes": nodes_list,
            "edges": edges_list
        }

    def save_skeleton(self, skeleton: Dict, output_dir: str = "skeletons") -> str:
        """Save skeleton to JSON file."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        skeleton_id = f"skeleton_{uuid.uuid4().hex[:8]}"
        file_path = os.path.join(output_dir, f"{skeleton_id}.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(skeleton, f, indent=2, ensure_ascii=False)

        print(f"Saved skeleton to {file_path}")
        return file_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate DAG skeletons.")
    parser.add_argument("--count", type=int, default=1, help="Number of skeletons to generate")
    parser.add_argument("--difficulty", type=int, default=10, help="Difficulty (node count)")
    parser.add_argument("--output", type=str, default="skeletons", help="Output directory")
    parser.add_argument("--distractor-type", type=str, default="none",
                        choices=["none", "A", "B", "both"],
                        help="Type of distractors: none (无干扰项), A (只有A类), B (只有B类), both (两种都有)")
    parser.add_argument("--droppable-ratio", type=float, default=0.3,
                        help="Ratio of droppable tools (with ITEM/HIDDEN_ITEM triggers) to use (0.0-1.0, default: 0.3)")
    parser.add_argument("--check-isomorphism", action="store_true",
                        help="Check and remove isomorphic DAGs after generation")
    
    args = parser.parse_args()
    
    # 导入同构检查模块（如果需要）
    check_isomorphism_func = None
    if args.check_isomorphism:
        try:
            from check_dag_isomorphism import check_isomorphism_in_directory
            check_isomorphism_func = check_isomorphism_in_directory
        except ImportError:
            print("⚠️  警告: 无法导入同构检查模块，将跳过同构检查")
    
    gen = DAGSkeletonGenerator(droppable_ratio=args.droppable_ratio)
    generated_count = 0
    removed_count = 0
    
    for i in range(args.count):
        print(f"Generating skeleton {i+1}/{args.count}...")
        skeleton = gen.generate_skeleton(args.difficulty, args.distractor_type)
        file_path = gen.save_skeleton(skeleton, args.output)
        
        # 检查同构
        if check_isomorphism_func:
            is_isomorphic, isomorphic_file = check_isomorphism_func(file_path, args.output)
            if is_isomorphic:
                print(f"  ⚠️  发现同构: 与 {isomorphic_file} 同构")
                print(f"  🗑️  删除同构文件: {os.path.basename(file_path)}")
                try:
                    os.remove(file_path)
                    removed_count += 1
                except Exception as e:
                    print(f"  ❌ 删除失败: {e}")
            else:
                generated_count += 1
        else:
            generated_count += 1
    
    print(f"\n{'='*60}")
    if args.check_isomorphism:
        print(f"生成统计:")
        print(f"  总尝试数: {args.count}")
        print(f"  保留文件数: {generated_count}")
        print(f"  删除同构数: {removed_count}")
    else:
        print(f"Generated {generated_count} skeleton(s)")