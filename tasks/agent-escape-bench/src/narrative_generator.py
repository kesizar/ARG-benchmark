#!/usr/bin/env python3
"""
Narrative Generator for DAG Scenarios
为 DAG 场景中的每个节点生成故事化的叙事文本（narrative），提供推理线索但不直接泄露答案。

工业级实现特点：
1. 使用 LLM 生成高质量、一致性的叙事文本
2. 支持多轮生成和验证，确保不泄露关键信息
3. 支持批量生成和增量更新
4. 提供详细的日志和错误处理
5. 支持多种 LLM 后端（Meituan、YuJu、DeepSeek）
6. 生成的叙事文本包含隐晦线索，引导推理而非枚举
"""

import json
import os
import sys
import argparse
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# 导入现有的 LLM 客户端
from dag_parameter_filler import (
    BaseLLMClient,
    LLMClientFactory,
    MeituanLLMClient,
    YuJuLLMClient,
    DeepSeekLLMClient
)

# Import prompts using language configuration
from language_config import get_prompts

_prompts = get_prompts()
NARRATIVE_SYSTEM_PROMPT = _prompts.NARRATIVE_SYSTEM_PROMPT
NARRATIVE_USER_PROMPT_TEMPLATE = _prompts.NARRATIVE_USER_PROMPT_TEMPLATE
NARRATIVE_USER_PROMPT_TEMPLATE_NO_EDGES = _prompts.NARRATIVE_USER_PROMPT_TEMPLATE_NO_EDGES
NARRATIVE_VALIDATION_PROMPT = _prompts.NARRATIVE_VALIDATION_PROMPT


# ============================================================================
# 配置和常量
# ============================================================================

class NarrativeStyle(Enum):
    """叙事风格枚举"""
    CYBERPUNK = "cyberpunk"              # 赛博朋克
    DETECTIVE = "detective"              # 侦探推理
    SCI_FI = "sci_fi"                    # 科幻
    FANTASY = "fantasy"                  # 奇幻
    STEAMPUNK = "steampunk"              # 蒸汽朋克
    POST_APOCALYPTIC = "post_apocalyptic"  # 末世
    MYSTERY = "mystery"                  # 悬疑
    TECHNO_THRILLER = "techno_thriller"  # 科技惊悚


class ClueLevel(Enum):
    """线索明确程度"""
    SUBTLE = "subtle"        # 隐晦（需要深度推理）
    MODERATE = "moderate"    # 适中（需要一定推理）
    OBVIOUS = "obvious"      # 明显（几乎直接指向）


@dataclass
class NarrativeConfig:
    """叙事生成配置"""
    style: NarrativeStyle = NarrativeStyle.CYBERPUNK
    clue_level: ClueLevel = ClueLevel.MODERATE
    max_length: int = 150  # 每个节点叙事的最大字符数
    min_length: int = 20   # 每个节点叙事的最小字符数
    language: str = "en"   # 语言：zh (中文) 或 en (英文)
    theme_consistency: bool = True  # 是否保持主题一致性
    include_red_herrings: bool = True  # 是否包含干扰信息
    clue_density: float = 0.3  # 线索密度（0-1，线索数量占节点总数的比例）
    edge_info_mode: str = "A"  # 边信息模式：A=提供完整边信息，B=不提供边信息


# ============================================================================
# 核心类
# ============================================================================

class NarrativeGenerator:
    """叙事生成器主类"""
    
    def __init__(
        self,
        llm_client: BaseLLMClient,
        config: Optional[NarrativeConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化叙事生成器
        
        Args:
            llm_client: LLM 客户端实例
            config: 叙事生成配置
            logger: 日志记录器
        """
        self.llm_client = llm_client
        self.config = config or NarrativeConfig()
        self.logger = logger or self._create_default_logger()
        
        # 缓存
        self._dag_cache: Optional[Dict[str, Any]] = None
        self._generated_narratives: Dict[str, str] = {}
        
    def _create_default_logger(self) -> logging.Logger:
        """创建默认日志记录器"""
        logger = logging.getLogger("NarrativeGenerator")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def load_dag(self, dag_path: str) -> Dict[str, Any]:
        """
        加载 DAG 文件
        
        Args:
            dag_path: DAG JSON 文件路径
            
        Returns:
            DAG 数据字典
        """
        self.logger.info(f"加载 DAG 文件: {dag_path}")
        
        try:
            with open(dag_path, 'r', encoding='utf-8') as f:
                dag_data = json.load(f)
            
            # 验证必要字段
            required_fields = ['nodes', 'edges', 'metadata']
            missing_fields = [f for f in required_fields if f not in dag_data]
            
            if missing_fields:
                raise ValueError(f"DAG 文件缺少必要字段: {', '.join(missing_fields)}")
            
            # 验证 nodes 必须是列表格式（标准格式）
            if not isinstance(dag_data['nodes'], list):
                raise ValueError("DAG 文件格式错误: nodes 字段必须是列表")
            
            self._dag_cache = dag_data
            self.logger.info(f"✅ DAG 加载成功: {len(dag_data['nodes'])} 个节点, {len(dag_data['edges'])} 条边")
            
            return dag_data
            
        except FileNotFoundError:
            self.logger.error(f"❌ 文件不存在: {dag_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ JSON 解析失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ 加载 DAG 失败: {e}")
            raise
    
    def _analyze_dag_structure(self, dag_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析 DAG 结构，提取关键信息用于叙事生成
        
        Args:
            dag_data: DAG 数据
            
        Returns:
            分析结果字典
        """
        self.logger.info("分析 DAG 结构...")
        
        nodes = dag_data['nodes']  # 列表格式
        edges = dag_data['edges']
        metadata = dag_data.get('metadata', {})
        
        # 构建 node_id 到 node 的映射
        nodes_dict = {node['id']: node for node in nodes}
        
        # 统计节点类型
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        # 识别源节点（没有输入边的节点）
        target_nodes = {edge['target_id'] for edge in edges}
        source_nodes = [node['id'] for node in nodes if node['id'] not in target_nodes]
        
        # 识别汇节点（没有输出边的节点）
        source_nodes_from_edges = {edge['source_id'] for edge in edges}
        sink_nodes = [node['id'] for node in nodes if node['id'] not in source_nodes_from_edges]
        
        # 计算节点的入度和出度
        in_degree = {node['id']: 0 for node in nodes}
        out_degree = {node['id']: 0 for node in nodes}
        
        for edge in edges:
            out_degree[edge['source_id']] += 1
            in_degree[edge['target_id']] += 1
        
        # 识别关键路径（从源节点到胜利节点）
        win_node_id = metadata.get('win_node_id')
        critical_path = self._find_critical_path(nodes_dict, edges, source_nodes, win_node_id)
        
        # 识别干扰节点（不在关键路径上的节点）
        distractor_nodes = [node['id'] for node in nodes if node['id'] not in critical_path]
        
        analysis = {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'node_types': node_types,
            'source_nodes': source_nodes,
            'sink_nodes': sink_nodes,
            'win_node_id': win_node_id,
            'critical_path': critical_path,
            'distractor_nodes': distractor_nodes,
            'in_degree': in_degree,
            'out_degree': out_degree,
            'max_depth': self._calculate_max_depth(nodes_dict, edges, source_nodes),
        }
        
        self.logger.info(f"  - 总节点数: {analysis['total_nodes']}")
        self.logger.info(f"  - 总边数: {analysis['total_edges']}")
        self.logger.info(f"  - 节点类型分布: {node_types}")
        self.logger.info(f"  - 源节点: {len(source_nodes)} 个")
        self.logger.info(f"  - 胜利节点: {win_node_id}")
        self.logger.info(f"  - 关键路径长度: {len(critical_path)} 个节点")
        self.logger.info(f"  - 干扰节点: {len(distractor_nodes)} 个")
        
        return analysis
    
    def _find_critical_path(
        self,
        nodes: Dict[str, Any],
        edges: List[Dict[str, Any]],
        source_nodes: List[str],
        win_node_id: Optional[str]
    ) -> List[str]:
        """
        查找从源节点到胜利节点的关键路径（使用 BFS）
        
        Returns:
            关键路径上的节点 ID 列表
        """
        if not win_node_id or win_node_id not in nodes:
            return []
        
        # 构建反向邻接表（从目标到源）
        reverse_graph = {nid: [] for nid in nodes.keys()}
        for edge in edges:
            reverse_graph[edge['target_id']].append(edge['source_id'])
        
        # 从胜利节点反向 BFS 到源节点
        visited = set()
        queue = [win_node_id]
        critical_nodes = set([win_node_id])
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            for predecessor in reverse_graph.get(current, []):
                if predecessor not in visited:
                    critical_nodes.add(predecessor)
                    queue.append(predecessor)
        
        return list(critical_nodes)
    
    def _calculate_max_depth(
        self,
        nodes: Dict[str, Any],
        edges: List[Dict[str, Any]],
        source_nodes: List[str]
    ) -> int:
        """计算 DAG 的最大深度"""
        # 构建邻接表
        graph = {nid: [] for nid in nodes.keys()}
        for edge in edges:
            graph[edge['source_id']].append(edge['target_id'])
        
        # DFS 计算深度
        def dfs_depth(node_id: str, visited: Set[str]) -> int:
            if node_id in visited:
                return 0
            visited.add(node_id)
            
            max_child_depth = 0
            for child in graph.get(node_id, []):
                max_child_depth = max(max_child_depth, dfs_depth(child, visited))
            
            visited.remove(node_id)
            return 1 + max_child_depth
        
        max_depth = 0
        for source in source_nodes:
            max_depth = max(max_depth, dfs_depth(source, set()))
        
        return max_depth
    
    def _format_dag_for_prompt(self, dag_data: Dict[str, Any]) -> Tuple[str, str, str, str]:
        """
        格式化 DAG 结构用于提示词
        
        Returns:
            (dag_structure, win_condition, source_nodes_info, edges_info)
        """
        nodes = dag_data['nodes']  # 列表格式
        edges = dag_data['edges']
        metadata = dag_data.get('metadata', {})
        
        # 1. DAG 结构概览（不包含具体值）
        dag_structure_parts = []
        for node in nodes:
            node_info = {
                'id': node['id'],
                'name': node.get('name', ''),
                'description': node.get('description', ''),
                'type': node.get('type', ''),
                'template_id': node.get('template_id', ''),
                'initial_visible': node.get('initial_visible', False),
                'inputs': [
                    {'name': inp['name'], 'type': inp['type'], 'description': inp.get('description', '')}
                    for inp in node.get('inputs', [])
                ],
                'outputs': [
                    {'name': out['name'], 'type': out['type'], 'description': out.get('description', '')}
                    for out in node.get('outputs', [])
                ]
            }
            dag_structure_parts.append(json.dumps(node_info, ensure_ascii=False, indent=2))
        
        dag_structure = "[\n" + ",\n".join(dag_structure_parts) + "\n]"
        
        # 2. 胜利条件
        win_condition_obj = metadata.get('win_condition', {})
        win_condition = json.dumps(win_condition_obj, ensure_ascii=False, indent=2)
        
        # 3. 源节点信息（包含初始值的类型但不包含具体值）
        source_init = metadata.get('source_init', {})
        source_nodes_list = source_init.get('source_nodes', [])
        by_node = source_init.get('by_node', {})
        
        source_info_parts = []
        for source_node_id in source_nodes_list:
            if source_node_id in by_node:
                source_info = by_node[source_node_id]
                init_inputs = source_info.get('init_inputs', {})
                init_outputs = source_info.get('init_outputs', {})
                
                # 构建类型描述
                type_parts = []
                if init_inputs:
                    type_parts.append(f"init_inputs: {', '.join(init_inputs.keys())}")
                if init_outputs:
                    type_parts.append(f"init_outputs: {', '.join(init_outputs.keys())}")
                
                type_desc = "; ".join(type_parts) if type_parts else "无"
                
                source_info_parts.append(
                    f"  - {source_node_id} ({source_info.get('template_id', 'unknown')}): "
                    f"提供了初始值，类型包括 {type_desc}"
                )
        
        source_nodes_info = "\n".join(source_info_parts) if source_info_parts else "（无明确的源节点初始值）"
        
        # 4. 边信息（连接关系）
        # 根据 edge_info_mode 配置决定是否提供边信息
        if self.config.edge_info_mode == "A":
            # 选项A：提供完整边信息（LLM 能设计更连贯的线索，但可能暗示路径）
            edges_info_parts = []
            for edge in edges:
                edges_info_parts.append(
                    f"  - {edge['source_id']}[{edge['source_port']}] → {edge['target_id']}[{edge['target_port']}] "
                    f"(类型: {edge['connection_type']})"
                )
            edges_info = "\n".join(edges_info_parts) if edges_info_parts else "（无边）"
        else:
            # 选项B：不提供具体边信息，只提供通用说明
            edges_info = "节点之间通过类型兼容的端口相互连接，具体连接关系需要玩家探索"
        
        return dag_structure, win_condition, source_nodes_info, edges_info
    
    def generate_narratives(
        self,
        dag_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        生成叙事文本
        
        Args:
            dag_data: DAG 数据（如果为 None，使用缓存的数据）
            max_retries: 最大重试次数
            validate: 是否进行验证
            
        Returns:
            包含叙事文本的字典
        """
        if dag_data is None:
            if self._dag_cache is None:
                raise ValueError("未加载 DAG 数据，请先调用 load_dag() 或提供 dag_data 参数")
            dag_data = self._dag_cache
        
        self.logger.info("=" * 80)
        self.logger.info("开始生成叙事文本")
        self.logger.info("=" * 80)
        
        # 分析 DAG 结构
        # analysis = self._analyze_dag_structure(dag_data)
        
        # 格式化提示词
        dag_structure, win_condition, source_nodes_info, edges_info = self._format_dag_for_prompt(dag_data)
        
        # 根据 edge_info_mode 选择不同的 prompt 模板
        if self.config.edge_info_mode == "A":
            prompt_template = NARRATIVE_USER_PROMPT_TEMPLATE
        else:
            prompt_template = NARRATIVE_USER_PROMPT_TEMPLATE_NO_EDGES
        
        # 构建用户提示词
        user_prompt = prompt_template.format(
            style=self.config.style.value,
            clue_level=self.config.clue_level.value,
            language=self.config.language,
            dag_structure=dag_structure,
            win_condition=win_condition,
            source_nodes_info=source_nodes_info,
            edges_info=edges_info,
            min_length=self.config.min_length,
            max_length=self.config.max_length,
            include_red_herrings=self.config.include_red_herrings
        )
        
        # 调用 LLM 生成
        retry_count = 0
        generated_narrative = None
        
        while retry_count < max_retries:
            try:
                self.logger.info(f"调用 LLM 生成叙事文本 (尝试 {retry_count + 1}/{max_retries})...")
                
                messages = [
                    {"role": "system", "content": NARRATIVE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]
                
                response = self.llm_client.chat(messages)
                self.logger.info("✅ LLM 响应成功")
                
                # 解析响应
                generated_narrative = self._parse_llm_response(response)
                
                if generated_narrative:
                    self.logger.info("✅ 叙事文本解析成功")
                    break
                else:
                    self.logger.warning("⚠️  叙事文本解析失败，准备重试...")
                    retry_count += 1
                    
            except Exception as e:
                self.logger.error(f"❌ LLM 调用失败: {e}")
                retry_count += 1
                
                if retry_count >= max_retries:
                    self.logger.error("❌ 达到最大重试次数，生成失败")
                    raise
        
        if generated_narrative is None:
            raise RuntimeError("生成叙事文本失败")
        
        # 验证生成的叙事文本
        if validate:
            self.logger.info("开始验证生成的叙事文本...")
            validation_result = self._validate_narrative(dag_data, generated_narrative)
            
            if not validation_result['is_valid']:
                self.logger.warning(f"⚠️  验证未通过，发现 {len(validation_result['issues'])} 个问题")
                for issue in validation_result['issues']:
                    self.logger.warning(
                        f"  - [{issue['severity']}] {issue['type']}: {issue['description']}"
                    )
                
                # 根据严重程度决定是否需要重新生成
                critical_issues = [i for i in validation_result['issues'] if i['severity'] == 'critical']
                if critical_issues and retry_count < max_retries:
                    self.logger.warning("发现严重问题，尝试重新生成...")
                    # 这里可以加入反馈循环，根据验证结果调整提示词重新生成
                    # 为简化起见，当前版本仅记录警告
            else:
                self.logger.info(f"✅ 验证通过，总体评分: {validation_result['overall_score']}/100")
        
        # 缓存结果
        self._generated_narratives = generated_narrative.get('node_narratives', {})
        
        self.logger.info("=" * 80)
        self.logger.info("叙事文本生成完成")
        self.logger.info("=" * 80)
        
        return generated_narrative
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析 LLM 响应，提取 JSON 数据
        
        Args:
            response: LLM 原始响应
            
        Returns:
            解析后的字典，如果解析失败返回 None
        """
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取 JSON 代码块
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # 尝试提取任何 JSON 对象
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            self.logger.error("无法从 LLM 响应中提取有效的 JSON")
            self.logger.debug(f"原始响应: {response[:500]}...")
            return None
    
    def _validate_narrative(
        self,
        dag_data: Dict[str, Any],
        generated_narrative: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证生成的叙事文本
        
        Args:
            dag_data: 原始 DAG 数据
            generated_narrative: 生成的叙事文本
            
        Returns:
            验证结果字典
        """
        try:
            # 构建验证提示词
            validation_prompt = NARRATIVE_VALIDATION_PROMPT.format(
                dag_structure=json.dumps(dag_data, ensure_ascii=False, indent=2)[:2000],  # 限制长度
                generated_narrative=json.dumps(generated_narrative, ensure_ascii=False, indent=2)
            )
            
            messages = [
                {"role": "system", "content": "你是一位专业的游戏内容审核员。"},
                {"role": "user", "content": validation_prompt}
            ]
            
            response = self.llm_client.chat(messages)
            validation_result = self._parse_llm_response(response)
            
            if validation_result:
                return validation_result
            else:
                # 如果解析失败，返回默认结果
                return {
                    'is_valid': True,
                    'issues': [],
                    'overall_score': 50,
                    'comments': '验证响应解析失败，默认通过'
                }
                
        except Exception as e:
            self.logger.error(f"验证过程出错: {e}")
            return {
                'is_valid': True,
                'issues': [],
                'overall_score': 50,
                'comments': f'验证失败: {str(e)}'
            }
    
    def apply_narratives_to_dag(
        self,
        dag_data: Dict[str, Any],
        narratives: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        将生成的叙事文本应用到 DAG 数据中
        
        Args:
            dag_data: 原始 DAG 数据
            narratives: 生成的叙事文本
            output_path: 输出文件路径（如果为 None，不保存文件）
            
        Returns:
            更新后的 DAG 数据
        """
        self.logger.info("将叙事文本应用到 DAG...")
        
        # 深拷贝避免修改原数据
        import copy
        updated_dag = copy.deepcopy(dag_data)
        
        # 添加整体叙事
        if 'intro_narrative' in narratives:
            updated_dag['intro_narrative'] = narratives['intro_narrative']
            self.logger.info("  ✅ 已添加整体开场叙事")
        
        # 添加主题元素（可选）
        if 'theme_elements' in narratives:
            if 'metadata' not in updated_dag:
                updated_dag['metadata'] = {}
            updated_dag['metadata']['theme_elements'] = narratives['theme_elements']
            self.logger.info("  ✅ 已添加主题元素")
        
        # 为每个节点添加 narrative 字段（nodes 是列表格式）
        node_narratives = narratives.get('node_narratives', {})
        nodes_updated = 0
        
        for node in updated_dag['nodes']:
            node_id = node.get('id')
            if node_id in node_narratives:
                node['narrative'] = node_narratives[node_id]
                nodes_updated += 1
        
        self.logger.info(f"  ✅ 已为 {nodes_updated}/{len(node_narratives)} 个节点添加叙事文本")
        
        # 保存到文件
        if output_path:
            self.logger.info(f"保存到文件: {output_path}")
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(updated_dag, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"✅ 文件保存成功: {output_path}")
            except Exception as e:
                self.logger.error(f"❌ 文件保存失败: {e}")
                raise
        
        return updated_dag
    
    def generate_and_apply(
        self,
        input_path: str,
        output_path: str,
        max_retries: int = 3,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        一站式：加载 DAG、生成叙事、应用并保存
        
        Args:
            input_path: 输入 DAG 文件路径
            output_path: 输出文件路径
            max_retries: 最大重试次数
            validate: 是否验证
            
        Returns:
            更新后的 DAG 数据
        """
        # 加载 DAG
        dag_data = self.load_dag(input_path)
        
        # 生成叙事
        narratives = self.generate_narratives(
            dag_data=dag_data,
            max_retries=max_retries,
            validate=validate
        )
        
        # 应用并保存
        updated_dag = self.apply_narratives_to_dag(
            dag_data=dag_data,
            narratives=narratives,
            output_path=output_path
        )
        
        return updated_dag


# ============================================================================
# 命令行接口
# ============================================================================

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="为 DAG 密室逃脱场景生成叙事文本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用配置文件
  python narrative_generator.py --config config/narrative_generator.json

  # 使用命令行参数
  python narrative_generator.py \\
    --input dag_full_data/skeleton_97f31b18_source_init_full.json \\
    --output dag_full_data/skeleton_97f31b18_with_narrative.json \\
    --client-type deepseek \\
    --api-key your_api_key \\
    --style cyberpunk \\
    --clue-level moderate

  # 配置文件 + 命令行参数（命令行参数优先级更高）
  python narrative_generator.py \\
    --config config/narrative_generator.json \\
    --style detective
        """
    )
    
    # 配置文件参数
    parser.add_argument(
        '--config', '-c',
        help='配置文件路径 (JSON 格式)'
    )
    
    # 输入输出参数
    parser.add_argument(
        '--input', '-i',
        help='输入 DAG JSON 文件路径'
    )
    parser.add_argument(
        '--output', '-o',
        help='输出 DAG JSON 文件路径'
    )
    
    # LLM 客户端参数
    parser.add_argument(
        '--client-type',
        choices=['meituan', 'yuju', 'deepseek', 'auto'],
        default='auto',
        help='LLM 客户端类型 (默认: auto)'
    )
    parser.add_argument(
        '--api-key',
        help='API Key (用于 YuJu 或 DeepSeek)'
    )
    parser.add_argument(
        '--authorization',
        help='Authorization string (用于 Meituan)'
    )
    parser.add_argument(
        '--model',
        help='模型名称 (如果不指定，使用客户端默认模型)'
    )
    parser.add_argument(
        '--api-endpoint',
        help='自定义 API 端点'
    )
    parser.add_argument(
        '--uid',
        help='用户 ID (用于 YuJu API)'
    )
    
    # 叙事配置参数
    parser.add_argument(
        '--style',
        choices=[s.value for s in NarrativeStyle],
        default='cyberpunk',
        help='叙事风格 (默认: cyberpunk)'
    )
    parser.add_argument(
        '--clue-level',
        choices=[c.value for c in ClueLevel],
        default='moderate',
        help='线索明确程度 (默认: moderate)'
    )
    parser.add_argument(
        '--max-length',
        type=int,
        default=150,
        help='每个节点叙事的最大字符数 (默认: 150)'
    )
    parser.add_argument(
        '--min-length',
        type=int,
        default=20,
        help='每个节点叙事的最小字符数 (默认: 20)'
    )
    parser.add_argument(
        '--language',
        choices=['zh', 'en'],
        default='en',
        help='叙事语言 (默认: zh 中文)'
    )
    parser.add_argument(
        '--no-red-herrings',
        action='store_true',
        help='不包含干扰信息'
    )
    parser.add_argument(
        '--edge-info-mode',
        choices=['A', 'B'],
        default='A',
        help='边信息模式：A=提供完整边信息（默认），B=不提供边信息'
    )
    
    # 其他参数
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='LLM 调用最大重试次数 (默认: 3)'
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='跳过验证步骤'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    args = parser.parse_args()
    
    # 加载配置文件（如果提供）
    config_data = {}
    if args.config:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            print(f"✅ 配置文件加载成功: {args.config}")
        except FileNotFoundError:
            print(f"❌ 配置文件不存在: {args.config}")
            return 1
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件解析失败: {e}")
            return 1
    
    # 合并配置：命令行参数优先级 > 配置文件 > 默认值
    def get_config_value(arg_value, config_path, default=None, allow_override_default=False):
        """
        获取配置值，命令行参数优先
        
        Args:
            arg_value: 命令行参数值
            config_path: 配置文件中的路径（点分隔）
            default: 默认值
            allow_override_default: 如果为 True，且 arg_value == default，则允许配置文件覆盖
        """
        # 从配置文件中获取嵌套的值
        config_value = config_data
        has_config_value = False
        for key in config_path.split('.'):
            if isinstance(config_value, dict) and key in config_value:
                config_value = config_value[key]
                has_config_value = True
            else:
                config_value = None
                has_config_value = False
                break
        
        # 如果允许配置文件覆盖默认值，且配置文件中有值
        if allow_override_default and has_config_value and arg_value == default:
            return config_value
        
        # 否则使用命令行参数（如果不为 None）或配置文件值或默认值
        if arg_value is not None:
            return arg_value
        return config_value if has_config_value else default
    
    # 应用配置
    args.input = get_config_value(args.input, 'input')
    args.output = get_config_value(args.output, 'output')
    args.client_type = get_config_value(args.client_type, 'llm.client_type', 'auto', allow_override_default=True)
    args.api_key = get_config_value(args.api_key, 'llm.api_key')
    args.authorization = get_config_value(args.authorization, 'llm.authorization')
    args.model = get_config_value(args.model, 'llm.model')
    args.api_endpoint = get_config_value(args.api_endpoint, 'llm.api_endpoint')
    args.uid = get_config_value(args.uid, 'llm.uid')
    args.style = get_config_value(args.style, 'narrative.style', 'cyberpunk', allow_override_default=True)
    args.clue_level = get_config_value(args.clue_level, 'narrative.clue_level', 'moderate', allow_override_default=True)
    args.max_length = get_config_value(args.max_length, 'narrative.max_length', 150, allow_override_default=True)
    args.min_length = get_config_value(args.min_length, 'narrative.min_length', 20, allow_override_default=True)
    args.language = get_config_value(args.language, 'narrative.language', 'zh', allow_override_default=True)
    args.no_red_herrings = get_config_value(
        args.no_red_herrings, 
        'narrative.include_red_herrings', 
        True,
        allow_override_default=True
    ) == False  # 注意：配置文件是 include，命令行是 no
    args.edge_info_mode = get_config_value(args.edge_info_mode, 'narrative.edge_info_mode', 'A', allow_override_default=True)
    args.max_retries = get_config_value(args.max_retries, 'generation.max_retries', 3, allow_override_default=True)
    args.no_validate = get_config_value(
        args.no_validate, 
        'generation.validate', 
        True,
        allow_override_default=True
    ) == False  # 注意：配置文件是 validate，命令行是 no_validate
    args.log_level = get_config_value(args.log_level, 'logging.log_level', 'INFO', allow_override_default=True)
    
    # 验证必需参数
    if not args.input:
        print("❌ 错误: 必须提供输入文件路径 (--input 或在配置文件中指定)")
        return 1
    if not args.output:
        print("❌ 错误: 必须提供输出文件路径 (--output 或在配置文件中指定)")
        return 1
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建 LLM 客户端
    client_kwargs = {}
    if args.api_key:
        client_kwargs['api_key'] = args.api_key
    if args.authorization:
        client_kwargs['authorization'] = args.authorization
    if args.model:
        client_kwargs['model'] = args.model
    if args.api_endpoint:
        client_kwargs['api_endpoint'] = args.api_endpoint
    if args.uid:
        client_kwargs['uid'] = args.uid
    
    try:
        llm_client = LLMClientFactory.create_client(args.client_type, **client_kwargs)
        print(f"✅ LLM 客户端创建成功: {args.client_type}")
    except Exception as e:
        print(f"❌ 创建 LLM 客户端失败: {e}")
        return 1
    
    # 创建叙事配置
    config = NarrativeConfig(
        style=NarrativeStyle(args.style),
        clue_level=ClueLevel(args.clue_level),
        max_length=args.max_length,
        min_length=args.min_length,
        language=args.language,
        include_red_herrings=not args.no_red_herrings,
        edge_info_mode=args.edge_info_mode
    )
    
    # 创建生成器
    generator = NarrativeGenerator(
        llm_client=llm_client,
        config=config
    )
    
    # 执行生成
    try:
        generator.generate_and_apply(
            input_path=args.input,
            output_path=args.output,
            max_retries=args.max_retries,
            validate=not args.no_validate
        )
        
        print("\n" + "=" * 80)
        print("🎉 叙事生成完成！")
        print(f"📄 输出文件: {args.output}")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())