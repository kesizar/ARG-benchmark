#!/usr/bin/env python3
"""
Narrative Generator V2 for DAG Scenarios
改进版叙事生成器 - 强调节点间的数据流和依赖关系

主要改进：
1. 在每个节点的 narrative 中明确说明其输入来自哪些上游节点
2. 保持命名一致性，使用模型生成的物品名称来引用节点
3. 使用新的 prompt_en_v2.py
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

# 导入新版本的 prompts
from prompt_en_v2 import (
    NARRATIVE_SYSTEM_PROMPT_V2,
    NARRATIVE_USER_PROMPT_TEMPLATE_V2,
    NARRATIVE_VALIDATION_PROMPT_V2
)


# ============================================================================
# 配置和常量
# ============================================================================

class NarrativeStyle(Enum):
    """叙事风格枚举"""
    CYBERPUNK = "cyberpunk"
    DETECTIVE = "detective"
    SCI_FI = "sci_fi"
    FANTASY = "fantasy"
    STEAMPUNK = "steampunk"
    POST_APOCALYPTIC = "post_apocalyptic"
    MYSTERY = "mystery"
    TECHNO_THRILLER = "techno_thriller"


@dataclass
class NarrativeConfig:
    """叙事生成配置 V2"""
    style: NarrativeStyle = NarrativeStyle.CYBERPUNK
    max_length: int = 200  # 增加到 200，因为需要描述数据流
    min_length: int = 50   # 增加到 50，确保有足够空间描述依赖
    theme_consistency: bool = True  # 保持命名和主题一致性


# ============================================================================
# 核心类
# ============================================================================

class NarrativeGeneratorV2:
    """叙事生成器 V2 主类"""
    
    def __init__(
        self,
        llm_client: BaseLLMClient,
        config: Optional[NarrativeConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化叙事生成器 V2
        
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
        logger = logging.getLogger("NarrativeGeneratorV2")
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
        self.logger.info(f"Loading DAG file: {dag_path}")
        
        try:
            with open(dag_path, 'r', encoding='utf-8') as f:
                dag_data = json.load(f)
            
            # 验证必要字段
            required_fields = ['nodes', 'edges', 'metadata']
            missing_fields = [f for f in required_fields if f not in dag_data]
            
            if missing_fields:
                raise ValueError(f"DAG file missing required fields: {', '.join(missing_fields)}")
            
            # 验证 nodes 必须是列表格式
            if not isinstance(dag_data['nodes'], list):
                raise ValueError("DAG format error: nodes field must be a list")
            
            self._dag_cache = dag_data
            self.logger.info(f"✅ DAG loaded: {len(dag_data['nodes'])} nodes, {len(dag_data['edges'])} edges")
            
            return dag_data
            
        except FileNotFoundError:
            self.logger.error(f"❌ File not found: {dag_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ JSON parse error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Failed to load DAG: {e}")
            raise
    
    def _format_dag_for_prompt(self, dag_data: Dict[str, Any]) -> Tuple[str, str, str, str]:
        """
        格式化 DAG 结构用于提示词
        V2 版本：强调边信息和数据流
        
        Returns:
            (dag_structure, win_condition, source_nodes_info, edges_info)
        """
        nodes = dag_data['nodes']
        edges = dag_data['edges']
        metadata = dag_data.get('metadata', {})
        
        # 1. DAG 结构概览
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
        
        # 3. 源节点信息
        source_init = metadata.get('source_init', {})
        source_nodes_list = source_init.get('source_nodes', [])
        by_node = source_init.get('by_node', {})
        
        source_info_parts = []
        for source_node_id in source_nodes_list:
            if source_node_id in by_node:
                source_info = by_node[source_node_id]
                init_inputs = source_info.get('init_inputs', {})
                init_outputs = source_info.get('init_outputs', {})
                
                type_parts = []
                if init_inputs:
                    type_parts.append(f"init_inputs: {', '.join(init_inputs.keys())}")
                if init_outputs:
                    type_parts.append(f"init_outputs: {', '.join(init_outputs.keys())}")
                
                type_desc = "; ".join(type_parts) if type_parts else "None"
                
                source_info_parts.append(
                    f"  - {source_node_id} ({source_info.get('template_id', 'unknown')}): "
                    f"Provides initial values, types include {type_desc}"
                )
        
        source_nodes_info = "\n".join(source_info_parts) if source_info_parts else "(No explicit source node initial values)"
        
        # 4. 边信息 - V2 版本：详细的数据流描述
        edges_info_parts = []
        edges_info_parts.append("**Data Flow Relationships:**\n")
        
        # 按目标节点分组边，方便看出哪些节点有多个输入
        edges_by_target = {}
        for edge in edges:
            target_id = edge['target_id']
            if target_id not in edges_by_target:
                edges_by_target[target_id] = []
            edges_by_target[target_id].append(edge)
        
        # 格式化边信息
        for target_id, target_edges in sorted(edges_by_target.items()):
            if len(target_edges) == 1:
                edge = target_edges[0]
                edges_info_parts.append(
                    f"  • Node '{target_id}' receives input from Node '{edge['source_id']}'\n"
                    f"    - Connection: {edge['source_id']}[{edge['source_port']}] → {target_id}[{edge['target_port']}]\n"
                    f"    - Type: {edge['connection_type']}"
                )
            else:
                source_ids = [e['source_id'] for e in target_edges]
                edges_info_parts.append(
                    f"  • Node '{target_id}' receives inputs from MULTIPLE nodes: {', '.join(source_ids)}"
                )
                for edge in target_edges:
                    edges_info_parts.append(
                        f"    - {edge['source_id']}[{edge['source_port']}] → {target_id}[{edge['target_port']}] (Type: {edge['connection_type']})"
                    )
        
        edges_info = "\n".join(edges_info_parts)
        
        return dag_structure, win_condition, source_nodes_info, edges_info
    
    def generate_narratives(
        self,
        dag_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        validate: bool = False
    ) -> Dict[str, Any]:
        """
        生成叙事文本 V2
        
        Args:
            dag_data: DAG 数据（如果为 None，使用缓存的数据）
            max_retries: 最大重试次数
            validate: 是否进行验证
            
        Returns:
            包含叙事文本的字典
        """
        if dag_data is None:
            if self._dag_cache is None:
                raise ValueError("No DAG data loaded, please call load_dag() first or provide dag_data parameter")
            dag_data = self._dag_cache
        
        self.logger.info("=" * 80)
        self.logger.info("Starting Narrative Generation V2")
        self.logger.info("=" * 80)
        
        # 格式化提示词
        dag_structure, win_condition, source_nodes_info, edges_info = self._format_dag_for_prompt(dag_data)
        
        # 构建用户提示词（V2 版本只有一个模板）
        user_prompt = NARRATIVE_USER_PROMPT_TEMPLATE_V2.format(
            style=self.config.style.value,
            dag_structure=dag_structure,
            win_condition=win_condition,
            source_nodes_info=source_nodes_info,
            edges_info=edges_info,
            min_length=self.config.min_length,
            max_length=self.config.max_length
        )
        
        # 调用 LLM 生成
        retry_count = 0
        generated_narrative = None
        
        while retry_count < max_retries:
            try:
                self.logger.info(f"Calling LLM to generate narratives (attempt {retry_count + 1}/{max_retries})...")
                
                messages = [
                    {"role": "system", "content": NARRATIVE_SYSTEM_PROMPT_V2},
                    {"role": "user", "content": user_prompt}
                ]
                
                response = self.llm_client.chat(messages)
                self.logger.info("✅ LLM response received")
                
                # 解析响应
                generated_narrative = self._parse_llm_response(response)
                
                if generated_narrative:
                    self.logger.info("✅ Narrative parsing successful")
                    break
                else:
                    self.logger.warning("⚠️  Narrative parsing failed, retrying...")
                    retry_count += 1
                    
            except Exception as e:
                self.logger.error(f"❌ LLM call failed: {e}")
                retry_count += 1
                
                if retry_count >= max_retries:
                    self.logger.error("❌ Maximum retries reached, generation failed")
                    raise
        
        if generated_narrative is None:
            raise RuntimeError("Failed to generate narratives")
        
        # 验证生成的叙事文本
        if validate:
            self.logger.info("Starting validation of generated narratives...")
            validation_result = self._validate_narrative(dag_data, generated_narrative)
            
            if not validation_result.get('is_valid', False):
                self.logger.warning(f"⚠️  Validation failed, found {len(validation_result.get('issues', []))} issues")
                for issue in validation_result.get('issues', []):
                    self.logger.warning(
                        f"  - [{issue.get('severity', 'unknown')}] {issue.get('type', 'unknown')}: {issue.get('description', 'N/A')}"
                    )
            else:
                self.logger.info(f"✅ Validation passed, overall score: {validation_result.get('overall_score', 0)}/100")
        
        # 缓存结果
        self._generated_narratives = generated_narrative.get('node_narratives', {})
        
        self.logger.info("=" * 80)
        self.logger.info("Narrative Generation V2 Complete")
        self.logger.info("=" * 80)
        
        return generated_narrative
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析 LLM 响应，提取 JSON 格式的叙事文本
        
        Args:
            response: LLM 的原始响应
            
        Returns:
            解析后的字典，或 None 如果解析失败
        """
        try:
            # 尝试直接解析为 JSON
            narrative_data = json.loads(response)
            
            # 验证必要字段
            if 'intro_narrative' not in narrative_data or 'node_narratives' not in narrative_data:
                self.logger.error("Missing required fields in response")
                return None
            
            return narrative_data
            
        except json.JSONDecodeError:
            # 尝试提取 JSON 代码块
            self.logger.warning("Response is not pure JSON, trying to extract JSON block...")
            
            # 匹配 ```json ... ``` 或 ``` ... ```
            json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            if matches:
                try:
                    narrative_data = json.loads(matches[0])
                    
                    if 'intro_narrative' in narrative_data and 'node_narratives' in narrative_data:
                        self.logger.info("✅ Successfully extracted JSON from code block")
                        return narrative_data
                except json.JSONDecodeError:
                    pass
            
            self.logger.error("Failed to parse response as JSON")
            return None
    
    def _validate_narrative(self, dag_data: Dict[str, Any], generated_narrative: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证生成的叙事文本
        
        Args:
            dag_data: 原始 DAG 数据
            generated_narrative: 生成的叙事文本
            
        Returns:
            验证结果字典
        """
        self.logger.info("Validating generated narratives...")
        
        # 简单的验证逻辑
        issues = []
        
        # 检查是否所有节点都有 narrative
        node_ids = {node['id'] for node in dag_data['nodes']}
        generated_node_ids = set(generated_narrative.get('node_narratives', {}).keys())
        
        missing_nodes = node_ids - generated_node_ids
        if missing_nodes:
            issues.append({
                'type': 'missing_narratives',
                'severity': 'critical',
                'description': f"Missing narratives for nodes: {', '.join(missing_nodes)}"
            })
        
        # 检查 narrative 长度
        for node_id, narrative in generated_narrative.get('node_narratives', {}).items():
            if len(narrative) < self.config.min_length:
                issues.append({
                    'type': 'too_short',
                    'severity': 'warning',
                    'description': f"Narrative for {node_id} is too short ({len(narrative)} chars)"
                })
            elif len(narrative) > self.config.max_length * 2:  # 允许一些超出
                issues.append({
                    'type': 'too_long',
                    'severity': 'warning',
                    'description': f"Narrative for {node_id} is too long ({len(narrative)} chars)"
                })
        
        # 计算总体评分
        overall_score = 100 - len(issues) * 10
        overall_score = max(0, overall_score)
        
        return {
            'is_valid': len([i for i in issues if i['severity'] == 'critical']) == 0,
            'issues': issues,
            'overall_score': overall_score
        }
    
    def generate_and_apply(
        self,
        input_path: str,
        output_path: str,
        max_retries: int = 3,
        validate: bool = False
    ):
        """
        生成叙事文本并应用到 DAG 文件
        
        Args:
            input_path: 输入 DAG 文件路径
            output_path: 输出文件路径
            max_retries: 最大重试次数
            validate: 是否验证
        """
        # 加载 DAG
        dag_data = self.load_dag(input_path)
        
        # 生成叙事
        generated_narrative = self.generate_narratives(
            dag_data=dag_data,
            max_retries=max_retries,
            validate=validate
        )
        
        # 应用到 DAG
        self.logger.info("Applying narratives to DAG...")
        
        # 更新 intro_narrative
        if 'intro_narrative' in generated_narrative:
            dag_data['metadata']['intro_narrative'] = generated_narrative['intro_narrative']
        
        # 记录使用的 narrative style
        dag_data['metadata']['narrative_style'] = self.config.style.value
        self.logger.info(f"  ✅ Recorded narrative style: {self.config.style.value}")
        
        # 更新每个节点的 narrative
        node_narratives = generated_narrative.get('node_narratives', {})
        for node in dag_data['nodes']:
            if node['id'] in node_narratives:
                node['narrative'] = node_narratives[node['id']]
                self.logger.info(f"  ✅ Applied narrative to node: {node['id']}")
        
        # 保存结果
        self.logger.info(f"Saving result to: {output_path}")
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dag_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ Results saved to: {output_path}")


# ============================================================================
# 命令行接口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Narrative Generator V2 - Enhanced with explicit data flow descriptions"
    )
    
    # 配置文件参数
    parser.add_argument('--config', '-c', help='Config file path (JSON format)')
    
    # 输入输出
    parser.add_argument('--input', '-i', help='Input DAG JSON file path')
    parser.add_argument('--output', '-o', help='Output file path')
    
    # LLM 配置
    parser.add_argument('--llm-type', choices=['meituan', 'yuju', 'deepseek', 'openai'], 
                       default='deepseek', help='LLM client type')
    parser.add_argument('--api-key', help='API key (if required)')
    parser.add_argument('--authorization', help='Authorization token (for Meituan LLM)')
    parser.add_argument('--model', help='Model name')
    parser.add_argument('--api-endpoint', help='API endpoint URL')
    parser.add_argument('--uid', help='User ID (for YuJu API)')
    
    # 叙事配置
    parser.add_argument('--style', choices=[s.value for s in NarrativeStyle],
                       default='cyberpunk', help='Narrative style')
    parser.add_argument('--max-length', type=int, default=200, 
                       help='Maximum narrative length per node')
    parser.add_argument('--min-length', type=int, default=50,
                       help='Minimum narrative length per node')
    
    # 生成配置
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry attempts')
    parser.add_argument('--validate', action='store_true', help='Validate generated narratives')
    
    args = parser.parse_args()
    
    # 加载配置文件（如果提供）
    config_data = {}
    if args.config:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            print(f"✅ Config file loaded: {args.config}")
        except FileNotFoundError:
            print(f"❌ Config file not found: {args.config}")
            return 1
        except json.JSONDecodeError as e:
            print(f"❌ Config file parse error: {e}")
            return 1
    
    # 合并配置：命令行参数优先级 > 配置文件 > 默认值
    def get_config_value(arg_value, config_path, default=None, allow_override_default=False):
        """Get config value, command line args take priority"""
        # Get nested value from config file
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
        
        # If allow override and config has value and arg is default
        if allow_override_default and has_config_value and arg_value == default:
            return config_value
        
        # Otherwise use command line arg (if not None) or config value or default
        if arg_value is not None:
            return arg_value
        return config_value if has_config_value else default
    
    # Apply config
    args.input = get_config_value(args.input, 'input')
    args.output = get_config_value(args.output, 'output')
    args.llm_type = get_config_value(args.llm_type, 'llm.client_type', 'deepseek', allow_override_default=True)
    args.api_key = get_config_value(args.api_key, 'llm.api_key')
    args.authorization = get_config_value(args.authorization, 'llm.authorization')
    args.model = get_config_value(args.model, 'llm.model')
    args.api_endpoint = get_config_value(args.api_endpoint, 'llm.api_endpoint')
    args.uid = get_config_value(args.uid, 'llm.uid')
    args.style = get_config_value(args.style, 'narrative.style', 'cyberpunk', allow_override_default=True)
    args.max_length = get_config_value(args.max_length, 'narrative.max_length', 200, allow_override_default=True)
    args.min_length = get_config_value(args.min_length, 'narrative.min_length', 50, allow_override_default=True)
    args.max_retries = get_config_value(args.max_retries, 'generation.max_retries', 3, allow_override_default=True)
    
    # Handle validate flag from config
    if not args.validate and config_data:
        config_validate = config_data.get('generation', {}).get('validate', False)
        if config_validate:
            args.validate = True
    
    # Validate required arguments
    if not args.input:
        print("❌ Error: --input is required")
        return 1
    if not args.output:
        print("❌ Error: --output is required")
        return 1
    
    # 创建 LLM 客户端
    print("=" * 80)
    print("Narrative Generator V2")
    print("=" * 80)
    print(f"\nCreating {args.llm_type} LLM client...")
    
    # Prepare LLM client kwargs
    llm_kwargs = {
        'client_type': args.llm_type,
        'api_key': args.api_key,
        'authorization': args.authorization,
        'model': args.model,
        'api_endpoint': args.api_endpoint
    }
    
    # Add uid for YuJu client
    if args.llm_type == 'yuju' and args.uid:
        llm_kwargs['uid'] = args.uid
    
    llm_client = LLMClientFactory.create_client(**llm_kwargs)
    
    # 创建叙事配置
    config = NarrativeConfig(
        style=NarrativeStyle(args.style),
        max_length=args.max_length,
        min_length=args.min_length
    )
    
    # 创建生成器
    generator = NarrativeGeneratorV2(
        llm_client=llm_client,
        config=config
    )
    
    # 执行生成
    try:
        generator.generate_and_apply(
            input_path=args.input,
            output_path=args.output,
            max_retries=args.max_retries,
            validate=args.validate
        )
        
        print("\n" + "=" * 80)
        print("🎉 Narrative Generation V2 Complete!")
        print(f"📄 Output file: {args.output}")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())