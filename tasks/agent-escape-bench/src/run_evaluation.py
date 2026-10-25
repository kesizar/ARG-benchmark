#!/usr/bin/env python3
"""
Industrial-grade evaluation launcher script
Supports single evaluation, batch evaluation, configuration files, command-line parameters, etc.
"""
import sys
import os
import argparse
import json
import glob
from pathlib import Path
from typing import List, Dict, Any

# Set language before importing other modules
import language_config
if '--language' in sys.argv:
    lang_idx = sys.argv.index('--language')
    if lang_idx + 1 < len(sys.argv):
        language_config.set_language(sys.argv[lang_idx + 1])

from agents import create_agent, list_agent_types, get_recommended_agent_type
from evaluator import EscapeRoomEvaluator


def load_config(config_file: str) -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)


def get_case_files(pattern: str) -> List[str]:
    """获取匹配模式的案例文件"""
    files = glob.glob(pattern, recursive=True)
    if not files:
        print(f"Error: No files found matching pattern: {pattern}")
        sys.exit(1)
    return sorted(files)


def create_agent_factory(args):
    """创建 agent 工厂函数"""
    def factory():
        # 构建额外参数
        extra_params = {}
        if hasattr(args, 'use_function_calling'):
            extra_params['use_function_calling'] = args.use_function_calling
        if hasattr(args, 'store'):
            extra_params['store'] = args.store
        if hasattr(args, 'enable_thinking') and args.enable_thinking is not None:
            extra_params['enable_thinking'] = args.enable_thinking
        if hasattr(args, 'thinking_level'):
            extra_params['thinking_level'] = args.thinking_level
        if hasattr(args, 'reasoning_effort'):
            extra_params['reasoning_effort'] = args.reasoning_effort
        if hasattr(args, 'reasoning_split') and args.reasoning_split is not None:
            extra_params['reasoning_split'] = args.reasoning_split
        
        # 构建 default_headers（如果提供了 uid）
        if hasattr(args, 'uid') and args.uid:
            extra_params['default_headers'] = {"uid": args.uid}
        
        logger.info(f"Creating agent with max_history_messages={args.max_history}")
        return create_agent(
            agent_type=args.agent_type,
            model=args.model,
            api_key=args.api_key,
            base_url=args.base_url,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            max_history_messages=args.max_history,
            max_retries=args.max_retries,
            **extra_params
        )
    return factory


def run_single_evaluation(args):
    """运行单个案例评测"""
    print("="*80)
    print("Single Case Evaluation")
    print("="*80)
    print(f"Case file: {args.case_file}")
    print(f"Model: {args.model}")
    print(f"Server: {args.server_url}")
    print("="*80)
    print()
    
    # 创建评测器
    evaluator = EscapeRoomEvaluator(
        server_url=args.server_url,
        max_steps=args.max_steps,
        timeout=args.timeout,
        verbose=args.verbose,
        output_dir=args.output_dir
    )
    
    # 创建 agent
    extra_params = {}
    if hasattr(args, 'use_function_calling'):
        extra_params['use_function_calling'] = args.use_function_calling
    if hasattr(args, 'store'):
        extra_params['store'] = args.store
    if hasattr(args, 'enable_thinking') and args.enable_thinking is not None:
        extra_params['enable_thinking'] = args.enable_thinking
    if hasattr(args, 'thinking_level'):
        extra_params['thinking_level'] = args.thinking_level
    if hasattr(args, 'reasoning_effort'):
        extra_params['reasoning_effort'] = args.reasoning_effort
    
    # 构建 default_headers（如果提供了 uid）
    if hasattr(args, 'uid') and args.uid:
        extra_params['default_headers'] = {"uid": args.uid}
    
    agent = create_agent(
        agent_type=args.agent_type,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        max_history_messages=args.max_history,
        max_retries=args.max_retries,
        **extra_params
    )
    
    # 运行评测
    try:
        result = evaluator.run_evaluation(
            agent=agent,
            case_file_path=args.case_file,
            save_result=True
        )
        
        # 打印总结
        print_result_summary(result)
        
        # 返回状态码
        sys.exit(0 if result.success else 1)
        
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_batch_evaluation(args):
    """运行批量评测"""
    # 获取所有案例文件
    case_files = get_case_files(args.case_pattern)
    
    print("="*80)
    print("Batch Evaluation")
    print("="*80)
    print(f"Case pattern: {args.case_pattern}")
    print(f"Found {len(case_files)} cases")
    print(f"Model: {args.model}")
    print(f"Server: {args.server_url}")
    print("="*80)
    print()
    
    # 创建评测器
    evaluator = EscapeRoomEvaluator(
        server_url=args.server_url,
        max_steps=args.max_steps,
        timeout=args.timeout,
        verbose=args.verbose,
        output_dir=args.output_dir
    )
    
    # 创建 agent 工厂
    agent_factory = create_agent_factory(args)
    
    # 运行批量评测
    try:
        results = evaluator.run_batch_evaluation(
            agent_factory=agent_factory,
            case_files=case_files,
            max_workers=args.max_workers
        )
        
        # 打印总结
        print_batch_summary(results)
        
        # 如果所有案例都成功则返回 0
        success_count = sum(1 for r in results if r.get('success', False))
        sys.exit(0 if success_count == len(results) else 1)
        
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def print_result_summary(result):
    """打印单个评测结果总结"""
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    print(f"{'Success:':<20} {'✅ Yes' if result.success else '❌ No'}")
    print(f"{'Case ID:':<20} {result.case_id}")
    print(f"{'Total Steps:':<20} {result.total_steps}")
    print(f"{'Tool Calls:':<20} {result.tool_calls}")
    print(f"{'Investigations:':<20} {result.investigations}")
    print(f"{'Failed Actions:':<20} {result.failed_actions}")
    print(f"{'Total Time:':<20} {result.total_time:.2f}s")
    
    if result.victory_string:
        print(f"{'Victory:':<20} {result.victory_string[:60]}...")
    
    if result.error_message:
        print(f"{'Error:':<20} {result.error_message[:60]}...")
    
    if result.agent_stats:
        print(f"\n{'Agent Statistics:':=^80}")
        print(f"{'API Calls:':<20} {result.agent_stats.get('api_calls', 0)}")
        print(f"{'Total Tokens:':<20} {result.agent_stats.get('total_tokens', 0)}")
        print(f"{'Estimated Cost:':<20} ${result.agent_stats.get('total_cost_usd', 0):.4f}")
    
    print("="*80)


def print_batch_summary(results: List[Dict[str, Any]]):
    """打印批量评测结果总结"""
    total = len(results)
    successful = sum(1 for r in results if r.get('success', False))
    failed = total - successful
    success_rate = successful / total if total > 0 else 0
    
    # 计算平均统计
    avg_steps = sum(r.get('total_steps', 0) for r in results) / max(total, 1)
    avg_time = sum(r.get('total_time', 0) for r in results) / max(total, 1)
    total_tokens = sum(r.get('agent_stats', {}).get('total_tokens', 0) for r in results)
    total_cost = sum(r.get('agent_stats', {}).get('total_cost_usd', 0) for r in results)
    
    print("\n" + "="*80)
    print("BATCH EVALUATION SUMMARY")
    print("="*80)
    print(f"{'Total Cases:':<25} {total}")
    print(f"{'Successful:':<25} ✅ {successful} ({success_rate*100:.1f}%)")
    print(f"{'Failed:':<25} ❌ {failed}")
    print(f"{'Average Steps:':<25} {avg_steps:.1f}")
    print(f"{'Average Time:':<25} {avg_time:.1f}s")
    print(f"{'Total Tokens:':<25} {total_tokens}")
    print(f"{'Total Cost:':<25} ${total_cost:.4f}")
    print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description="AgentEscapeBench Evaluation Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use config file (recommended - all parameters in one file)
  python run_evaluation.py --config config/gpt-5.json
  
  # Single case evaluation with command line args
  python run_evaluation.py --case-file dag_full_data/skeleton_xxx.json --api-key sk-xxx
  
  # Config file + override case file
  python run_evaluation.py --config config/gpt-5.json --case-file another_case.json
  
  # Batch evaluation
  python run_evaluation.py --batch --case-pattern "dag_full_data/*.json" --api-key sk-xxx
  
  # Custom model and parameters (override config)
  python run_evaluation.py --config config/gpt-5.json --temperature 0.5 --max-steps 30
        """
    )
    
    # 主要参数
    parser.add_argument('--case-file', '-f', type=str, 
                        help='Single case file to evaluate')
    parser.add_argument('--batch', '-b', action='store_true', 
                        help='Run batch evaluation')
    parser.add_argument('--case-pattern', '-p', type=str, 
                        help='File pattern for batch evaluation (e.g., "dag_full_data/*.json")')
    parser.add_argument('--config', '-c', type=str, 
                        help='Load configuration from JSON file')
    
    # Server parameters
    parser.add_argument('--server-url', '-s', type=str, default="http://localhost:8000", 
                        help='Server URL (default: http://localhost:8000)')
    parser.add_argument('--max-steps', type=int, default=50, 
                        help='Maximum steps per evaluation (default: 50)')
    parser.add_argument('--timeout', type=int, default=1500, 
                        help='Timeout in seconds (default: 1500)')
    
    # Language and model parameters
    parser.add_argument('--language', '-l', type=str,
                        choices=['en', 'zh'],
                        default='en',
                        help='Language for prompts: en (English) or zh (Chinese) (default: en)')
    parser.add_argument('--agent-type', '-a', type=str,
                        choices=['chat_completions', 'responses', 'deepseek_chat', 'deepseek_reasoner', 'gemini', 'doubao', 'qwen', 'minimax', 'auto'],
                        default='auto',
                        help='Agent type: chat_completions, responses, deepseek_chat, deepseek_reasoner, gemini, doubao, qwen, minimax, or auto (default: auto, auto-detect based on model)')
    parser.add_argument('--model', '-m', type=str, default="gpt-4", 
                        help='Model name (default: gpt-4)')
    parser.add_argument('--api-key', type=str, default=None, 
                        help='OpenAI API key (default: from OPENAI_API_KEY env)')
    parser.add_argument('--base-url', type=str, default=None, 
                        help='Custom API base URL')
    parser.add_argument('--temperature', type=float, default=0.7, 
                        help='Sampling temperature (default: 0.7)')
    parser.add_argument('--max-tokens', type=int, default=8192, 
                        help='Maximum tokens per request (default: 1500)')
    parser.add_argument('--max-history', type=int, default=100, 
                        help='Maximum conversation history messages (default: 100)')
    parser.add_argument('--max-retries', type=int, default=3, 
                        help='Maximum API retries (default: 3)')
    
    # Agent 特定参数
    parser.add_argument('--use-function-calling', action='store_true', default=True,
                        help='Use OpenAI Function Calling (for chat_completions, default: True)')
    parser.add_argument('--no-function-calling', action='store_true',
                        help='Disable Function Calling (use pure JSON mode)')
    parser.add_argument('--store', action='store_true', default=False,
                        help='Store responses for state management (for responses API, default: False)')
    parser.add_argument('--enable-thinking', type=lambda x: x.lower() == 'true', default=None,
                        help='Enable thinking mode (for deepseek_reasoner/doubao, default: None, use agent default)')
    parser.add_argument('--thinking-level', type=str, 
                        choices=['minimal', 'low', 'medium', 'high'],
                        default='medium',
                        help='Thinking level for Gemini (minimal/low/medium/high, default: medium)')
    parser.add_argument('--reasoning-effort', type=str,
                        choices=['minimal', 'low', 'medium', 'high'],
                        default='medium',
                        help='Reasoning effort for Doubao (minimal/low/medium/high, default: medium)')
    parser.add_argument('--reasoning-split', type=lambda x: x.lower() == 'true',
                        default=None,
                        help='Split reasoning content for MiniMax (true/false, default: None, use agent default)')
    parser.add_argument('--uid', type=str, default=None,
                        help='User ID for custom headers (e.g., for YuJu platform: "")')  # 已删除**
    
    # 输出参数
    parser.add_argument('--output-dir', '-o', type=str, default="evaluation_results", 
                        help='Output directory (default: evaluation_results)')
    parser.add_argument('--verbose', '-v', action='store_true', default=True, 
                        help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true', 
                        help='Quiet mode (minimal output)')
    
    # 批量评测参数
    parser.add_argument('--max-workers', type=int, default=1, 
                        help='Maximum concurrent workers for batch evaluation (default: 1)')
    
    args = parser.parse_args()
    
    # 处理配置文件
    if args.config:
        config = load_config(args.config)
        # 首先保存原始命令行参数（用于判断是否被用户显式设置）
        parser_defaults = {
            'max_steps': 50,
            'max_history': 100,
            'temperature': 0.7,
            'max_tokens': 8192,
            'max_retries': 3,
            'timeout': 1500,
            'server_url': "http://localhost:8000",
            'output_dir': "evaluation_results",
            'model': "gpt-4",
            'agent_type': 'auto',
        }
        
        # 配置文件中的值会被命令行参数覆盖（仅当命令行参数被显式设置时）
        for key, value in config.items():
            # 如果属性不存在，直接设置
            if not hasattr(args, key):
                setattr(args, key, value)
            # 如果命令行值等于默认值，说明用户没有显式设置，使用配置文件的值
            elif key in parser_defaults and getattr(args, key) == parser_defaults[key]:
                setattr(args, key, value)
            # 如果命令行值为 None，使用配置文件的值
            elif getattr(args, key) is None:
                setattr(args, key, value)
    
    # 处理 quiet 模式
    if args.quiet:
        args.verbose = False
    
    # 处理 function calling 参数
    if args.no_function_calling:
        args.use_function_calling = False
    
    # 自动检测 agent type
    if args.agent_type == 'auto':
        args.agent_type = get_recommended_agent_type(args.model)
        if args.verbose:
            print(f"Auto-detected agent type: {args.agent_type}")
    
    # 检查 API key
    if not args.api_key:
        args.api_key = os.environ.get("OPENAI_API_KEY")
        if not args.api_key:
            print("Error: OPENAI_API_KEY not provided")
            print("Please set it with:")
            print("  export OPENAI_API_KEY='your-api-key'")
            print("Or use --api-key argument or add 'api_key' in config file")
            sys.exit(1)
    
    # 决定运行模式
    if args.batch:
        if not args.case_pattern:
            print("Error: --case-pattern required for batch evaluation")
            sys.exit(1)
        run_batch_evaluation(args)
    elif args.case_file:
        # case_file 可以来自命令行或配置文件
        if not os.path.exists(args.case_file):
            print(f"Error: File not found: {args.case_file}")
            sys.exit(1)
        run_single_evaluation(args)
    else:
        # 如果使用了配置文件但没有指定 case_file，给出更友好的提示
        if args.config:
            print("Error: No case file specified")
            print("Please specify case file with --case-file or add 'case_file' in config file")
        else:
            parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()