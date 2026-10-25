#!/usr/bin/env python3
"""
Batch Evaluation Script for Multiple Difficulty Levels

This script runs parallel evaluations across multiple difficulty levels (5, 10, 15)
for a given model configuration. It supports concurrent evaluation of multiple
JSON files within each difficulty level to speed up the process.

Usage:
    python batch_evaluate.py --config config/kimi-k2-yuju.json --parallel 4
    python batch_evaluate.py --config config/gpt-4o.json --difficulties 5 10 --parallel 2
    python batch_evaluate.py --config config/deepseek-chat.json --data-dir data_en_filtered --parallel 8
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Tuple


class BatchEvaluator:
    """Batch evaluator for multiple difficulty levels with parallel execution."""
    
    def __init__(
        self,
        config_file: str = None,
        config_5: str = None,
        config_10: str = None,
        config_15: str = None,
        data_dir: str = "data_en_filtered",
        difficulties: List[int] = [5, 10, 15],
        parallel_workers: int = 4,
        skip_completed: bool = True,
        verbose: bool = True
    ):
        """
        Initialize batch evaluator.
        
        Args:
            config_file: Path to default model configuration JSON file (for all difficulties)
            config_5: Path to config for difficulty 5 (overrides config_file)
            config_10: Path to config for difficulty 10 (overrides config_file)
            config_15: Path to config for difficulty 15 (overrides config_file)
            data_dir: Base directory containing difficulty subdirectories
            difficulties: List of difficulty levels to evaluate
            parallel_workers: Number of parallel workers per difficulty
            skip_completed: Whether to skip already completed evaluations
            verbose: Whether to print verbose output
        """
        self.data_dir = Path(data_dir)
        self.difficulties = difficulties
        self.parallel_workers = parallel_workers
        self.skip_completed = skip_completed
        self.verbose = verbose
        
        # Build config mapping for each difficulty
        self.difficulty_configs = {}
        
        # Use difficulty-specific configs if provided, otherwise use default
        difficulty_config_map = {
            5: config_5,
            10: config_10,
            15: config_15
        }
        
        for diff in difficulties:
            config_path = difficulty_config_map.get(diff) or config_file
            if config_path:
                config_path = Path(config_path)
                if not config_path.exists():
                    raise FileNotFoundError(f"Config file not found: {config_path}")
                
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                self.difficulty_configs[diff] = {
                    'config_file': config_path,
                    'config': config,
                    'model_name': config.get('model', 'unknown_model'),
                    'output_dir': config.get('output_dir', 'evaluation_results')
                }
        
        if not self.difficulty_configs:
            raise ValueError("No valid config file provided. Use --config or --config-5/10/15")
        
        # Use the first config's model name and output dir as defaults
        first_config = list(self.difficulty_configs.values())[0]
        self.model_name = first_config['model_name']
        self.output_base_dir = first_config['output_dir']
        
        # Statistics
        self.total_cases = 0
        self.completed_cases = 0
        self.success_cases = 0
        self.failed_cases = 0
        self.start_time = None
        self.end_time = None
    
    def log(self, message: str, level: str = "INFO"):
        """Print log message with timestamp."""
        if self.verbose or level == "ERROR":
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def get_case_files(self, difficulty: int) -> List[Path]:
        """
        Get all narrative JSON files for a given difficulty level.
        
        Args:
            difficulty: Difficulty level (5, 10, or 15)
            
        Returns:
            List of Path objects to narrative JSON files
        """
        narrative_dir = self.data_dir / str(difficulty) / "narrative"
        
        if not narrative_dir.exists():
            self.log(f"Narrative directory not found: {narrative_dir}", "ERROR")
            return []
        
        case_files = sorted(narrative_dir.glob("skeleton_*.json"))
        return case_files
    
    def is_case_completed(self, case_file: Path, difficulty: int) -> bool:
        """
        Check if a case has already been evaluated (regardless of success/failure).
        
        Args:
            case_file: Path to the case JSON file
            difficulty: Difficulty level
            
        Returns:
            True if the case result file exists and has valid content
        """
        if not self.skip_completed:
            return False
        
        case_name = case_file.stem
        
        # Get output directory for this difficulty
        config_info = self.difficulty_configs.get(difficulty)
        if not config_info:
            return False
        
        output_dir = Path(config_info['output_dir']) / str(difficulty)
        result_file = output_dir / f"{case_name}_result.json"
        
        # Check if result file exists
        if not result_file.exists():
            return False
        
        # Check if the evaluation was completed (regardless of success/failure)
        try:
            with open(result_file, 'r') as f:
                result_data = json.load(f)
            
            # Consider it completed if the file has valid content
            # (has case_id and either success field or trajectory)
            if 'case_id' in result_data:
                return True
        except Exception as e:
            self.log(f"Error reading result file {result_file}: {e}", "ERROR")
            return False
        
        return False
    
    def run_single_evaluation(self, case_file: Path, difficulty: int) -> Tuple[bool, str, float]:
        """
        Run evaluation for a single case file.
        
        Args:
            case_file: Path to the case JSON file
            difficulty: Difficulty level
            
        Returns:
            Tuple of (success, case_name, duration)
        """
        case_name = case_file.stem
        start_time = time.time()
        
        # Get config for this difficulty
        config_info = self.difficulty_configs.get(difficulty)
        if not config_info:
            self.log(f"No config found for difficulty {difficulty}", "ERROR")
            return False, case_name, 0
        
        # Update config with case file
        temp_config = config_info['config'].copy()
        temp_config['case_file'] = str(case_file)
        
        # Update output directory to include difficulty
        output_dir = Path(config_info['output_dir']) / str(difficulty)
        temp_config['output_dir'] = str(output_dir)
        
        # Create temporary config file
        temp_config_file = Path(f".temp_config_{difficulty}_{case_name}.json")
        with open(temp_config_file, 'w') as f:
            json.dump(temp_config, f, indent=2)
        
        try:
            # Run evaluation
            cmd = [
                sys.executable,
                "run_evaluation.py",
                "--config", str(temp_config_file)
            ]
            
            if self.verbose:
                self.log(f"[Difficulty {difficulty}] Evaluating {case_name}...")
            
            # Run subprocess with timeout
            timeout = temp_config.get('timeout', 1500) + 60  # Add buffer
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            if success:
                self.log(f"[Difficulty {difficulty}] ✅ {case_name} completed in {duration:.1f}s")
            else:
                self.log(f"[Difficulty {difficulty}] ❌ {case_name} failed (exit code: {result.returncode})", "ERROR")
                if self.verbose and result.stderr:
                    self.log(f"Error output: {result.stderr[:500]}", "ERROR")
            
            return success, case_name, duration
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.log(f"[Difficulty {difficulty}] ⏱️  {case_name} timed out after {duration:.1f}s", "ERROR")
            return False, case_name, duration
            
        except Exception as e:
            duration = time.time() - start_time
            self.log(f"[Difficulty {difficulty}] ❌ {case_name} error: {e}", "ERROR")
            return False, case_name, duration
            
        finally:
            # Clean up temporary config file
            if temp_config_file.exists():
                temp_config_file.unlink()
    
    def evaluate_difficulty_level(self, difficulty: int) -> Dict:
        """
        Evaluate all cases for a given difficulty level in parallel.
        
        Args:
            difficulty: Difficulty level (5, 10, or 15)
            
        Returns:
            Dictionary with evaluation results
        """
        self.log("=" * 80)
        self.log(f"Evaluating Difficulty Level {difficulty}")
        self.log("=" * 80)
        
        # Get config info for this difficulty
        config_info = self.difficulty_configs.get(difficulty)
        if config_info:
            self.log(f"Config: {config_info['config_file']}")
            self.log(f"Model: {config_info['model_name']}")
            self.log(f"Max steps: {config_info['config'].get('max_steps', 'N/A')}")
            self.log(f"Timeout: {config_info['config'].get('timeout', 'N/A')}s")
        
        # Get case files
        case_files = self.get_case_files(difficulty)
        
        if not case_files:
            self.log(f"No case files found for difficulty {difficulty}", "ERROR")
            return {
                'difficulty': difficulty,
                'total': 0,
                'completed': 0,
                'success': 0,
                'failed': 0,
                'skipped': 0,
                'duration': 0
            }
        
        # Filter out already completed cases
        if self.skip_completed:
            original_count = len(case_files)
            case_files_to_run = []
            skipped_files = []
            
            for case_file in case_files:
                if self.is_case_completed(case_file, difficulty):
                    skipped_files.append(case_file)
                else:
                    case_files_to_run.append(case_file)
            
            case_files = case_files_to_run
            skipped_count = len(skipped_files)
            
            if skipped_count > 0:
                self.log(f"Skipping {skipped_count} already completed cases")
                if self.verbose and skipped_count <= 10:
                    for f in skipped_files:
                        self.log(f"  ✓ {f.stem} (already completed)")
        else:
            skipped_count = 0
        
        self.log(f"Found {len(case_files)} cases to evaluate for difficulty {difficulty}")
        self.log(f"Using {self.parallel_workers} parallel workers")
        self.log("")
        
        # Track results
        results = {
            'difficulty': difficulty,
            'total': len(case_files) + skipped_count,  # Total including skipped
            'to_evaluate': len(case_files),  # Only those that need evaluation
            'completed': 0,
            'success': 0,
            'failed': 0,
            'skipped': skipped_count,
            'cases': [],
            'start_time': time.time()
        }
        
        # Run evaluations in parallel
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # Submit all tasks
            future_to_case = {
                executor.submit(self.run_single_evaluation, case_file, difficulty): case_file
                for case_file in case_files
            }
            
            # Process completed tasks
            for future in as_completed(future_to_case):
                case_file = future_to_case[future]
                try:
                    success, case_name, duration = future.result()
                    results['completed'] += 1
                    
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                    
                    results['cases'].append({
                        'name': case_name,
                        'success': success,
                        'duration': duration
                    })
                    
                    # Print progress
                    total_evaluated = results['completed']
                    total_to_evaluate = results['to_evaluate']
                    if total_to_evaluate > 0:
                        progress = total_evaluated / total_to_evaluate * 100
                    else:
                        progress = 100.0
                    self.log(f"Progress: {total_evaluated}/{total_to_evaluate} ({progress:.1f}%) "
                           f"- Success: {results['success']}, Failed: {results['failed']}")
                    
                except Exception as e:
                    self.log(f"Exception processing {case_file.name}: {e}", "ERROR")
                    results['failed'] += 1
        
        results['duration'] = time.time() - results['start_time']
        
        # Print summary for this difficulty
        self.log("")
        self.log("=" * 80)
        self.log(f"Difficulty {difficulty} Summary")
        self.log("=" * 80)
        self.log(f"Total cases: {results['total']}")
        if results['skipped'] > 0:
            self.log(f"Skipped (already completed): {results['skipped']}")
            self.log(f"Evaluated: {results['completed']}")
        else:
            self.log(f"Evaluated: {results['completed']}")
        self.log(f"Success: {results['success']}")
        self.log(f"Failed: {results['failed']}")
        if results['total'] > 0:
            self.log(f"Overall success rate: {results['success']/results['total']*100:.1f}%")
        if results['to_evaluate'] > 0:
            self.log(f"Evaluated success rate: {results['success']/results['to_evaluate']*100:.1f}%")
        self.log(f"Duration: {results['duration']:.1f}s ({results['duration']/60:.1f} min)")
        self.log("")
        
        return results
    
    def run_batch_evaluation(self) -> Dict:
        """
        Run batch evaluation across all difficulty levels.
        
        Returns:
            Dictionary with overall evaluation results
        """
        self.log("=" * 80)
        self.log("Batch Evaluation - Multiple Difficulty Levels")
        self.log("=" * 80)
        self.log(f"Model: {self.model_name}")
        self.log(f"Data directory: {self.data_dir}")
        self.log(f"Difficulty levels: {self.difficulties}")
        self.log(f"Parallel workers per level: {self.parallel_workers}")
        self.log(f"Skip completed: {self.skip_completed}")
        self.log("")
        self.log("Configuration per difficulty:")
        for diff in self.difficulties:
            config_info = self.difficulty_configs.get(diff)
            if config_info:
                self.log(f"  Difficulty {diff}: {config_info['config_file'].name} "
                       f"(max_steps={config_info['config'].get('max_steps', 'N/A')}, "
                       f"timeout={config_info['config'].get('timeout', 'N/A')}s)")
        self.log("=" * 80)
        self.log("")
        
        self.start_time = time.time()
        all_results = []
        
        # Evaluate each difficulty level sequentially
        # (parallel within each level, sequential across levels)
        for difficulty in self.difficulties:
            difficulty_results = self.evaluate_difficulty_level(difficulty)
            all_results.append(difficulty_results)
            
            # Update global statistics
            self.total_cases += difficulty_results['total']
            self.completed_cases += difficulty_results['completed']
            self.success_cases += difficulty_results['success']
            self.failed_cases += difficulty_results['failed']
        
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        # Print overall summary
        self.print_overall_summary(all_results, total_duration)
        
        # Save summary to file
        summary_file = Path(self.output_base_dir) / f"batch_summary_{int(time.time())}.json"
        self.save_summary(all_results, total_duration, summary_file)
        
        return {
            'all_results': all_results,
            'total_cases': self.total_cases,
            'completed_cases': self.completed_cases,
            'success_cases': self.success_cases,
            'failed_cases': self.failed_cases,
            'total_duration': total_duration
        }
    
    def print_overall_summary(self, all_results: List[Dict], total_duration: float):
        """Print overall evaluation summary."""
        self.log("")
        self.log("=" * 80)
        self.log("OVERALL EVALUATION SUMMARY")
        self.log("=" * 80)
        self.log(f"Model: {self.model_name}")
        self.log(f"Total difficulty levels: {len(self.difficulties)}")
        self.log("")
        
        # Per-difficulty breakdown
        for result in all_results:
            diff = result['difficulty']
            success_rate = result['success'] / result['total'] * 100 if result['total'] > 0 else 0
            self.log(f"Difficulty {diff}:")
            self.log(f"  Cases: {result['total']}")
            self.log(f"  Success: {result['success']} ({success_rate:.1f}%)")
            self.log(f"  Failed: {result['failed']}")
            self.log(f"  Duration: {result['duration']:.1f}s ({result['duration']/60:.1f} min)")
            self.log("")
        
        # Overall statistics
        overall_success_rate = self.success_cases / self.total_cases * 100 if self.total_cases > 0 else 0
        self.log("Overall Statistics:")
        self.log(f"  Total cases: {self.total_cases}")
        self.log(f"  Completed: {self.completed_cases}")
        self.log(f"  Success: {self.success_cases} ({overall_success_rate:.1f}%)")
        self.log(f"  Failed: {self.failed_cases}")
        self.log(f"  Total duration: {total_duration:.1f}s ({total_duration/60:.1f} min, {total_duration/3600:.2f} hours)")
        
        if self.total_cases > 0:
            avg_time_per_case = total_duration / self.total_cases
            self.log(f"  Average time per case: {avg_time_per_case:.1f}s")
        
        self.log("=" * 80)
    
    def save_summary(self, all_results: List[Dict], total_duration: float, output_file: Path):
        """Save evaluation summary to JSON file."""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Build config files info
        config_files_info = {}
        for diff, config_info in self.difficulty_configs.items():
            config_files_info[f'difficulty_{diff}'] = str(config_info['config_file'])
        
        summary = {
            'model': self.model_name,
            'config_files': config_files_info,
            'data_directory': str(self.data_dir),
            'difficulties': self.difficulties,
            'parallel_workers': self.parallel_workers,
            'skip_completed': self.skip_completed,
            'timestamp': datetime.now().isoformat(),
            'total_cases': self.total_cases,
            'completed_cases': self.completed_cases,
            'success_cases': self.success_cases,
            'failed_cases': self.failed_cases,
            'total_duration_seconds': total_duration,
            'results_by_difficulty': all_results
        }
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log(f"Summary saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch Evaluation Script for Multiple Difficulty Levels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic: Evaluate all difficulties with same config (4 parallel workers)
  python batch_evaluate.py --config config/kimi-k2-yuju.json --parallel 4
  
  # Use different configs for different difficulties
  python batch_evaluate.py \\
    --config-5 config/model_5.json \\
    --config-10 config/model_10.json \\
    --config-15 config/model_15.json \\
    --parallel 4
  
  # Resume interrupted evaluation (automatically skips completed cases)
  python batch_evaluate.py --config config/gpt-4o.json --parallel 4
  
  # Re-run all cases (ignore completed ones)
  python batch_evaluate.py --config config/gpt-4o.json --parallel 4 --no-skip-completed
  
  # Evaluate only specific difficulties
  python batch_evaluate.py --config config/deepseek-chat.json --difficulties 5 10 --parallel 2
  
  # Use custom data directory
  python batch_evaluate.py --config config/gemini-3-pro-preview.json --data-dir data_en --parallel 8
  
  # Quiet mode
  python batch_evaluate.py --config config/qwen3-32b.json --parallel 4 --quiet
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        default=None,
        help='Path to model configuration JSON file (used for all difficulties if no specific config provided)'
    )
    
    parser.add_argument(
        '--config-5',
        type=str,
        default=None,
        help='Path to config for difficulty 5 (overrides --config)'
    )
    
    parser.add_argument(
        '--config-10',
        type=str,
        default=None,
        help='Path to config for difficulty 10 (overrides --config)'
    )
    
    parser.add_argument(
        '--config-15',
        type=str,
        default=None,
        help='Path to config for difficulty 15 (overrides --config)'
    )
    
    parser.add_argument(
        '--data-dir', '-d',
        type=str,
        default='data_en_filtered',
        help='Base directory containing difficulty subdirectories (default: data_en_filtered)'
    )
    
    parser.add_argument(
        '--difficulties',
        type=int,
        nargs='+',
        default=[5, 10, 15],
        help='Difficulty levels to evaluate (default: 5 10 15)'
    )
    
    parser.add_argument(
        '--parallel', '-p',
        type=int,
        default=4,
        help='Number of parallel workers per difficulty level (default: 4)'
    )
    
    parser.add_argument(
        '--skip-completed',
        action='store_true',
        default=True,
        help='Skip already completed evaluations (default: True)'
    )
    
    parser.add_argument(
        '--no-skip-completed',
        action='store_true',
        help='Do not skip completed evaluations, re-run all cases'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode (less verbose output)'
    )
    
    args = parser.parse_args()
    
    # Check if at least one config is provided
    if not args.config and not args.config_5 and not args.config_10 and not args.config_15:
        print("Error: At least one config file must be provided")
        print("Use --config for all difficulties, or --config-5/10/15 for specific difficulties")
        sys.exit(1)
    
    # Validate data directory
    if not Path(args.data_dir).exists():
        print(f"Error: Data directory not found: {args.data_dir}")
        sys.exit(1)
    
    # Handle skip_completed flag
    skip_completed = not args.no_skip_completed if args.no_skip_completed else args.skip_completed
    
    # Create evaluator and run
    try:
        evaluator = BatchEvaluator(
            config_file=args.config,
            config_5=args.config_5,
            config_10=args.config_10,
            config_15=args.config_15,
            data_dir=args.data_dir,
            difficulties=args.difficulties,
            parallel_workers=args.parallel,
            skip_completed=skip_completed,
            verbose=not args.quiet
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    try:
        results = evaluator.run_batch_evaluation()
        
        # Exit with success if all cases completed
        if results['failed_cases'] == 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nBatch evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()