"""
DAG Executor: Fills all node values in a DAG by executing nodes in topological order.
"""

import json
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict, deque
from models import GraphScenario, InterfaceType
from simulator import ToolSimulator


class NodeExecutionState:
    """Tracks the execution state of a single node."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.status = "pending"  # pending, ready, executing, completed, failed
        self.input_values: Dict[str, Any] = {}
        self.output_values: Dict[str, Any] = {}
        self.dependencies: List[str] = []
        self.error_message: str = None


class ValueFlow:
    """Records a value flow between two nodes."""

    def __init__(self, source_node: str, source_port: str,
                 target_node: str, target_port: str, value: Any, connection_type: str):
        self.source_node = source_node
        self.source_port = source_port
        self.target_node = target_node
        self.target_port = target_port
        self.value = value
        self.connection_type = connection_type


class ExecutionResult:
    """Result of DAG execution."""

    def __init__(self):
        self.success = False
        self.total_nodes = 0
        self.executed_nodes = 0
        self.failed_nodes: List[str] = []
        self.node_values: Dict[str, Dict[str, Any]] = {}  # node_id -> {input_values, output_values}
        self.execution_log: List[str] = []
        self.execution_time = 0.0
        self.value_flows: List[ValueFlow] = []


class DAGParser:
    """Parses DAG structure from JSON and builds graph representation."""

    def __init__(self, scenario: GraphScenario):
        self.scenario = scenario
        self.nodes = scenario.nodes
        self.edges = scenario.edges
        self.initial_values = self._extract_initial_values()
        self.adjacency_list = self._build_adjacency_list()
        self.reverse_adjacency_list = self._build_reverse_adjacency_list()

    def _extract_initial_values(self) -> Dict[str, Dict[str, Any]]:
        """Extract initial values from nodes.
        
        从节点的输入端口中提取 init_value 属性。
        这些属性是在 run_dag_executor.py 中动态添加的。
        """
        initial_values = {}

        for node_id, node in self.nodes.items():
            node_init_values = {}

            # Check individual port init_value fields
            for port in node.inputs:
                if hasattr(port, 'init_value') and port.init_value is not None:
                    node_init_values[port.name] = port.init_value

            if node_init_values:
                initial_values[node_id] = node_init_values

        return initial_values

    def _build_adjacency_list(self) -> Dict[str, List[Tuple[str, str, str]]]:
        """Build adjacency list: node_id -> [(target_node_id, source_port, target_port), ...]"""
        adj = defaultdict(list)

        for edge in self.edges:
            adj[edge.source_id].append((edge.target_id, edge.source_port, edge.target_port))

        return adj

    def _build_reverse_adjacency_list(self) -> Dict[str, List[Tuple[str, str, str]]]:
        """Build reverse adjacency list: node_id -> [(source_node_id, source_port, target_port), ...]"""
        rev_adj = defaultdict(list)

        for edge in self.edges:
            rev_adj[edge.target_id].append((edge.source_id, edge.source_port, edge.target_port))

        return rev_adj


class TopologicalSorter:
    """Performs topological sort on DAG to determine execution order."""

    def __init__(self, parser: DAGParser):
        self.parser = parser
        self.nodes = parser.nodes
        self.adjacency_list = parser.adjacency_list
        self.reverse_adjacency_list = parser.reverse_adjacency_list
        self.initial_values = parser.initial_values

    def sort(self) -> List[str]:
        """
        Perform topological sort using Kahn's algorithm.
        Returns list of node IDs in execution order.
        """
        # Calculate in-degree for each node
        in_degree = {node_id: 0 for node_id in self.nodes}

        for node_id in self.nodes:
            for target_id, _, _ in self.adjacency_list[node_id]:
                in_degree[target_id] += 1

        # Start with nodes that have no dependencies (in-degree = 0)
        # or nodes that have initial values
        queue = deque()

        for node_id in self.nodes:
            if in_degree[node_id] == 0:
                queue.append(node_id)

        execution_order = []

        while queue:
            node_id = queue.popleft()
            execution_order.append(node_id)

            # Process all neighbors
            for target_id, _, _ in self.adjacency_list[node_id]:
                in_degree[target_id] -= 1
                if in_degree[target_id] == 0:
                    queue.append(target_id)

        # Check for cycles
        if len(execution_order) != len(self.nodes):
            raise ValueError("DAG contains cycles or is disconnected")

        return execution_order

    def get_dependencies(self, node_id: str) -> List[str]:
        """Get all nodes that must be executed before this node."""
        dependencies = []
        for source_id, _, _ in self.reverse_adjacency_list[node_id]:
            dependencies.append(source_id)
        return dependencies


class ValuePropagator:
    """Propagates values through the DAG based on edges."""

    def __init__(self, parser: DAGParser):
        self.parser = parser
        self.nodes = parser.nodes
        self.edges = parser.edges
        self.adjacency_list = parser.adjacency_list
        self.reverse_adjacency_list = parser.reverse_adjacency_list

    def propagate_output(self, source_node_id: str, output_values: Dict[str, Any]) -> List[ValueFlow]:
        """
        Propagate output values from a node to its downstream nodes.
        Returns list of ValueFlow records.
        """
        value_flows = []

        # Find all edges starting from this node
        for target_node_id, source_port, target_port in self.adjacency_list[source_node_id]:
            if source_port in output_values:
                value = output_values[source_port]
                value_flows.append(ValueFlow(
                    source_node=source_node_id,
                    source_port=source_port,
                    target_node=target_node_id,
                    target_port=target_port,
                    value=value,
                    connection_type="data_flow"
                ))

        return value_flows

    def collect_input_values(self, node_id: str, node_values: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Collect all input values for a node from its upstream nodes.
        Returns dict of {port_name: value}.
        """
        input_values = {}

        # Find all edges pointing to this node
        for source_node_id, source_port, target_port in self.reverse_adjacency_list[node_id]:
            if source_node_id in node_values and 'output_values' in node_values[source_node_id]:
                source_outputs = node_values[source_node_id]['output_values']
                if source_port in source_outputs:
                    input_values[target_port] = source_outputs[source_port]

        return input_values


class NodeExecutor:
    """Executes individual nodes and manages their state."""

    def __init__(self, scenario: GraphScenario, simulator: ToolSimulator, raw_nodes_data: Dict[str, Any] = None):
        self.scenario = scenario
        self.simulator = simulator
        self.nodes = scenario.nodes
        self.raw_nodes_data = raw_nodes_data or {}

    def execute_node(self, node_id: str, input_values: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """
        Execute a single node.
        Returns (success, output_values, error_message).
        """
        node = self.nodes[node_id]

        try:
            if node.type == "Tool":
                return self._execute_tool(node_id, node, input_values)
            elif node.type == "Item":
                return self._execute_item(node_id, node, input_values)
            else:
                return False, {}, f"Unknown node type: {node.type}"

        except Exception as e:
            return False, {}, f"Execution error: {str(e)}"

    def _execute_tool(self, node_id: str, node, input_values: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """Execute a tool node."""
        try:
            # Get tool name from template_id if available, otherwise use node name
            tool_name = node.name
            if node_id in self.raw_nodes_data:
                template_id = self.raw_nodes_data[node_id].get('template_id')
                if template_id:
                    tool_name = template_id
            
            # Filter out ITEM/HIDDEN_ITEM input ports (trigger ports for droppable tools)
            # These ports are used for controlling node visibility but should not be passed to the tool function
            # Also merge init_value for ports without upstream values (source nodes)
            filtered_inputs = {}
            for port in node.inputs:
                if port.type not in [InterfaceType.ITEM, InterfaceType.HIDDEN_ITEM]:
                    if port.name in input_values:
                        # Value from upstream node
                        filtered_inputs[port.name] = input_values[port.name]
                    elif hasattr(port, 'init_value'):
                        # Value from metadata.initial_values (for source nodes)
                        filtered_inputs[port.name] = port.init_value
            
            # Add init outputs and inputs to input_values for terminals
            # Terminals don't compute, they just validate input and return init values
            tool_inputs = dict(filtered_inputs)  # Use filtered inputs
            if node_id in self.raw_nodes_data:
                init_data = self.raw_nodes_data[node_id].get('init', {})
                if 'outputs' in init_data:
                    tool_inputs['_init_outputs'] = init_data['outputs']
                if 'inputs' in init_data:
                    tool_inputs['_init_inputs'] = init_data['inputs']

            # Call simulator to execute the tool
            output_values = self.simulator.execute(tool_name, tool_inputs)
            
            # Check for unused ITEM/HIDDEN_ITEM output ports
            # 如果输出端口是 ITEM/HIDDEN_ITEM 类型但没有连接到下游节点，
            # 说明这是一个末端掉落，返回占位文本而不是创建新节点
            for output_port in node.outputs:
                if output_port.name not in output_values:
                    # Check if this port type is ITEM or HIDDEN_ITEM
                    if output_port.type in [InterfaceType.ITEM, InterfaceType.HIDDEN_ITEM]:
                        # Check if this output is actually used (connected to another node)
                        is_used = self._is_output_port_used(node_id, output_port.name)
                        if not is_used: #如果掉落东西但是没有下游节点
                            output_values[output_port.name] = "Dropped an irrelevant item"
            
            return True, output_values, None
        except Exception as e:
            return False, {}, f"Tool execution failed: {str(e)}"

    def _execute_item(self, node_id: str, node, input_values: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """Execute an item node (passive node, no actual execution).
        
        Item 节点的输出值应该从 init_outputs 中获取（信息源头）。
        在离线 DAG 执行时，init_outputs 通过 raw_nodes_data 传递。
        
        对于 ITEM/HIDDEN_ITEM 类型的输出端口：
        - 如果在 init_outputs 中有值，使用该值
        - 如果没有值且无出边（末端掉落），生成占位文本
        - 如果没有值但有出边（掉落关系），不填充 value（评测框架完全基于边类型和拓扑，不需要 value）
        """
        output_values = {}
        
        # 从 raw_nodes_data 的 init.outputs 中获取输出值
        # 这是 Item 节点作为信息源头的标准方式
        if node_id in self.raw_nodes_data:
            init_data = self.raw_nodes_data[node_id].get('init', {})
            if 'outputs' in init_data and init_data['outputs']:
                output_values.update(init_data['outputs'])
        
        # 处理 ITEM/HIDDEN_ITEM 类型的输出端口
        for output_port in node.outputs:
            if output_port.name not in output_values:
                # Check if this port type is ITEM or HIDDEN_ITEM
                if output_port.type in [InterfaceType.ITEM, InterfaceType.HIDDEN_ITEM]:
                    # Check if this output is actually used (connected to another node)
                    is_used = self._is_output_port_used(node_id, output_port.name)
                    if not is_used:
                        # 无出边（末端掉落）：生成占位文本
                        output_values[output_port.name] = "Dropped an irrelevant item"
                    # 如果有出边，不填充 value
                    # 评测框架 (server.py) 完全基于边的类型和拓扑关系处理掉落，不依赖 value 字段
        
        return True, output_values, None

    def _is_output_port_used(self, node_id: str, port_name: str) -> bool:
        """Check if an output port is used (connected to another node)."""
        # Look through all edges to see if this output port is connected
        for edge in self.scenario.edges:
            if edge.source_id == node_id and edge.source_port == port_name:
                return True
        return False


class DAGExecutor:
    """Main executor that orchestrates DAG execution."""

    def __init__(self, scenario: GraphScenario, simulator: ToolSimulator, raw_nodes_data: Dict[str, Any] = None):
        self.scenario = scenario
        self.simulator = simulator
        self.raw_nodes_data = raw_nodes_data or {}

        # Initialize components
        self.parser = DAGParser(scenario)
        self.sorter = TopologicalSorter(self.parser)
        self.propagator = ValuePropagator(self.parser)
        self.executor = NodeExecutor(scenario, simulator, raw_nodes_data)

        # Execution state
        self.node_states: Dict[str, NodeExecutionState] = {}
        self.node_values: Dict[str, Dict[str, Any]] = {}
        self.execution_log: List[str] = []
        self.value_flows: List[ValueFlow] = []

    def execute(self) -> ExecutionResult:
        """Execute the entire DAG and fill all node values."""
        result = ExecutionResult()
        result.total_nodes = len(self.scenario.nodes)

        try:
            # Step 1: Get execution order
            execution_order = self.sorter.sort()
            self.log(f"Execution order: {execution_order}")

            # Step 2: Initialize node states
            for node_id in self.scenario.nodes:
                self.node_states[node_id] = NodeExecutionState(node_id)
                self.node_values[node_id] = {"input_values": {}, "output_values": {}}

            # Step 3: Set initial values
            for node_id, init_values in self.parser.initial_values.items():
                self.node_values[node_id]["input_values"].update(init_values) # 这里的init_values只有init_input没有output
                self.node_states[node_id].input_values.update(init_values)
                self.log(f"Set initial values for {node_id}: {init_values}")

            # Step 4: Execute nodes in order
            for node_id in execution_order:
                self.log(f"\n--- Executing node: {node_id} ---")

                # Collect input values from upstream nodes
                collected_inputs = self.propagator.collect_input_values(node_id, self.node_values)

                # Merge with initial values
                all_inputs = {**self.node_values[node_id]["input_values"], **collected_inputs}

                self.log(f"Input values: {all_inputs}")

                # Execute the node
                success, output_values, error_msg = self.executor.execute_node(node_id, all_inputs)

                if success:
                    # Save complete input values (initial + propagated)
                    self.node_values[node_id]["input_values"] = all_inputs
                    self.node_states[node_id].input_values = all_inputs
                    
                    # Save output values
                    self.node_values[node_id]["output_values"] = output_values
                    self.node_states[node_id].output_values = output_values
                    self.node_states[node_id].status = "completed"
                    result.executed_nodes += 1
                    self.log(f"Output values: {output_values}")

                    # Propagate output values to downstream nodes
                    flows = self.propagator.propagate_output(node_id, output_values)
                    self.value_flows.extend(flows)

                    for flow in flows:
                        self.log(f"Propagate: {flow.source_node}.{flow.source_port} -> {flow.target_node}.{flow.target_port} = {flow.value}")
                else:
                    self.node_states[node_id].status = "failed"
                    self.node_states[node_id].error_message = error_msg
                    result.failed_nodes.append(node_id)
                    self.log(f"FAILED: {error_msg}")

            result.success = len(result.failed_nodes) == 0
            result.node_values = self.node_values
            result.execution_log = self.execution_log
            result.value_flows = self.value_flows

            self.log(f"\n=== Execution Summary ===")
            self.log(f"Total nodes: {result.total_nodes}")
            self.log(f"Executed: {result.executed_nodes}")
            self.log(f"Failed: {len(result.failed_nodes)}")
            self.log(f"Success: {result.success}")

            return result

        except Exception as e:
            result.success = False
            result.execution_log = self.execution_log
            self.log(f"FATAL ERROR: {str(e)}")
            return result

    def log(self, message: str):
        """Add message to execution log."""
        self.execution_log.append(message)
        print(message)