#!/usr/bin/env python3
"""
Sort complexity statistics CSV files based on multiple criteria.

Sorting criteria (in order of priority):
1. edge_count: higher is better
2. init_input_ports: lower is better (negative weight)
3. max_possible_edges: higher is better
4. drop_count: higher is better
"""

import pandas as pd
import sys
from pathlib import Path


def calculate_composite_score(row):
    """
    Calculate a composite score for ranking.
    
    Formula considers:
    - edge_count (positive: more edges = better)
    - init_input_ports (negative: fewer init inputs = better)
    - max_possible_edges (positive: more potential = better)
    - drop_count (positive: more drops = better)
    
    Weights are chosen to balance the importance of each metric.
    """
    # Normalize and weight each metric
    # Higher scores = better
    
    edge_score = row['edge_count'] * 10  # Weight: 10
    init_penalty = -row['init_input_ports'] * 8  # Weight: -8 (penalty for more inits)
    max_edges_score = row['max_possible_edges'] * 5  # Weight: 5
    drop_score = row['drop_count'] * 7  # Weight: 7
    
    composite = edge_score + init_penalty + max_edges_score + drop_score
    
    return composite


def sort_csv_file(input_path, output_path):
    """
    Sort a CSV file based on the composite score.
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to output sorted CSV file
    """
    # Read CSV
    df = pd.read_csv(input_path)
    
    # Calculate composite score
    df['composite_score'] = df.apply(calculate_composite_score, axis=1)
    
    # Sort by composite score (descending - higher is better)
    df_sorted = df.sort_values('composite_score', ascending=False)
    
    # Remove the composite_score column from output (optional - keep for transparency)
    # df_sorted = df_sorted.drop('composite_score', axis=1)
    
    # Save sorted CSV
    df_sorted.to_csv(output_path, index=False)
    
    print(f"✅ Sorted: {input_path.name}")
    print(f"   Output: {output_path.name}")
    print(f"   Total records: {len(df_sorted)}")
    print(f"   Score range: {df_sorted['composite_score'].min():.2f} to {df_sorted['composite_score'].max():.2f}")
    print()
    
    # Show top 5 entries
    print(f"   Top 5 entries:")
    for idx, row in df_sorted.head(5).iterrows():
        print(f"     {row['filename']}: "
              f"edges={row['edge_count']}, "
              f"init_inputs={row['init_input_ports']}, "
              f"max_edges={row['max_possible_edges']}, "
              f"drops={row['drop_count']}, "
              f"score={row['composite_score']:.2f}")
    print()


def main():
    """Main function to sort all complexity statistics files."""
    base_dir = Path(__file__).parent
    
    # Files to process
    difficulty_levels = [5, 10, 15]
    
    print("=" * 80)
    print("Complexity Statistics Sorting Tool")
    print("=" * 80)
    print()
    print("Sorting criteria:")
    print("  1. edge_count: higher is better (weight: 10)")
    print("  2. init_input_ports: lower is better (weight: -8)")
    print("  3. max_possible_edges: higher is better (weight: 5)")
    print("  4. drop_count: higher is better (weight: 7)")
    print()
    print("Composite score formula:")
    print("  score = edge_count*10 - init_input_ports*8 + max_possible_edges*5 + drop_count*7")
    print()
    print("=" * 80)
    print()
    
    for difficulty in difficulty_levels:
        input_file = base_dir / f"complexity_statistics_{difficulty}.csv"
        output_file = base_dir / f"complexity_statistics_{difficulty}_sorted.csv"
        
        if not input_file.exists():
            print(f"⚠️  File not found: {input_file.name}")
            continue
        
        sort_csv_file(input_file, output_file)
    
    print("=" * 80)
    print("✅ All files sorted successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()