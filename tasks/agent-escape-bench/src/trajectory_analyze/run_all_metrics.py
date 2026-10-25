#!/usr/bin/env python3
"""
批量计算所有模型、所有难度的细粒度指标

用法:
  # 计算全部模型、全部难度
  python run_all_metrics.py

  # 只计算指定模型
  python run_all_metrics.py --models deepseek-chat gpt-5

  # 只计算指定难度
  python run_all_metrics.py --difficulties 5 15

  # 同时指定模型和难度
  python run_all_metrics.py --models deepseek-chat gpt-5 --difficulties 15

  # 指定自定义路径
  python run_all_metrics.py --problem-base ../题目可解性验证/narrative_generate --eval-base ../final_eval --output-base results_cc
"""

import argparse
import os
import sys
import time

from compute_fine_grained_metrics import batch_compute_metrics


def discover_models(eval_base: str) -> list:
    """自动发现 eval_base 下所有模型目录（排除 -test 后缀）"""
    models = []
    for name in sorted(os.listdir(eval_base)):
        if name.endswith('-test'):
            continue
        path = os.path.join(eval_base, name)
        if os.path.isdir(path):
            models.append(name)
    return models


def discover_difficulties(eval_base: str, model: str) -> list:
    """自动发现某个模型下所有难度子目录"""
    model_dir = os.path.join(eval_base, model)
    difficulties = []
    for name in sorted(os.listdir(model_dir)):
        path = os.path.join(model_dir, name)
        if os.path.isdir(path) and name.isdigit():
            difficulties.append(name)
    return sorted(difficulties, key=int)


def main():
    parser = argparse.ArgumentParser(description='批量计算细粒度评测指标')
    parser.add_argument('--models', nargs='+', default=None,
                        help='要计算的模型列表（默认: 全部模型）')
    parser.add_argument('--difficulties', nargs='+', default=None,
                        help='要计算的难度列表（默认: 全部难度）')
    parser.add_argument('--problem-base', default='../题目可解性验证/narrative_generate',
                        help='题目文件根目录 (默认: ../题目可解性验证/narrative_generate)')
    parser.add_argument('--eval-base', default='../final_eval',
                        help='评测结果根目录 (默认: ../final_eval)')
    parser.add_argument('--output-base', default='results_cc',
                        help='输出目录 (默认: results_cc)')
    args = parser.parse_args()

    # 发现可用模型
    all_models = discover_models(args.eval_base)
    if args.models:
        # 验证用户指定的模型是否存在
        for m in args.models:
            if m not in all_models:
                print(f"Warning: model '{m}' not found in {args.eval_base}, skipping")
        models = [m for m in args.models if m in all_models]
    else:
        models = all_models

    if not models:
        print("No models to process.")
        sys.exit(1)

    # 收集所有 (model, difficulty) 任务
    tasks = []
    for model in models:
        available_difficulties = discover_difficulties(args.eval_base, model)
        if args.difficulties:
            difficulties = [d for d in args.difficulties if d in available_difficulties]
        else:
            difficulties = available_difficulties

        for diff in difficulties:
            problem_dir = os.path.join(args.problem_base, diff)
            result_dir = os.path.join(args.eval_base, model, diff)
            output_dir = os.path.join(args.output_base, model)
            output_file = os.path.join(output_dir, f'metrics_output_{diff}.json')

            if not os.path.isdir(problem_dir):
                print(f"Warning: problem dir not found: {problem_dir}, skipping")
                continue

            tasks.append((model, diff, problem_dir, result_dir, output_dir, output_file))

    print(f"{'='*60}")
    print(f"Models: {len(models)}  |  Tasks: {len(tasks)}")
    print(f"{'='*60}")

    # 执行
    success_count = 0
    fail_count = 0
    total_start = time.time()

    for i, (model, diff, problem_dir, result_dir, output_dir, output_file) in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] {model} / difficulty={diff}")
        print(f"  problem: {problem_dir}")
        print(f"  results: {result_dir}")
        print(f"  output:  {output_file}")

        os.makedirs(output_dir, exist_ok=True)

        try:
            t0 = time.time()
            batch_compute_metrics(problem_dir, result_dir, output_file)
            elapsed = time.time() - t0
            print(f"  Done in {elapsed:.1f}s")
            success_count += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            fail_count += 1

    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"Finished: {success_count} success, {fail_count} failed, {total_elapsed:.1f}s total")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
