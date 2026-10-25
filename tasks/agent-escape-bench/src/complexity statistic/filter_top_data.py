#!/usr/bin/env python3
"""
Filter and copy top N data files based on sorted complexity statistics.

This script reads the sorted CSV files and copies the corresponding data files
from data_en to data_en_filtered directory.
"""

import pandas as pd
import shutil
import os
from pathlib import Path


def copy_data_files(skeleton_filename, source_difficulty_dir, target_difficulty_dir):
    """
    Copy all related files for a given skeleton to the target directory.
    
    Args:
        skeleton_filename: The skeleton filename (e.g., 'skeleton_abc123.json')
        source_difficulty_dir: Source directory path (e.g., 'data_en/5')
        target_difficulty_dir: Target directory path (e.g., 'data_en_filtered/5')
    
    Returns:
        Tuple of (success_count, failed_count)
    """
    basename = skeleton_filename.replace('.json', '')
    
    # Define subdirectories and their corresponding file patterns
    subdirs_patterns = [
        ('dag', f'{basename}.json'),
        ('sources', f'{basename}.json'),
        ('inits', f'{basename}.json'),
        ('full', f'{basename}.json'),
        ('narrative', f'{basename}.json'),
    ]
    
    success_count = 0
    failed_count = 0
    
    for subdir, filename in subdirs_patterns:
        source_file = source_difficulty_dir / subdir / filename
        target_subdir = target_difficulty_dir / subdir
        target_file = target_subdir / filename
        
        # Create target subdirectory if it doesn't exist
        target_subdir.mkdir(parents=True, exist_ok=True)
        
        # Copy file if it exists
        if source_file.exists():
            try:
                shutil.copy2(source_file, target_file)
                success_count += 1
            except Exception as e:
                print(f"    ⚠️  Failed to copy {source_file.name} from {subdir}/: {e}")
                failed_count += 1
        else:
            print(f"    ⚠️  File not found: {source_file.relative_to(source_file.parent.parent.parent)}")
            failed_count += 1
    
    return success_count, failed_count


def filter_and_copy_top_n(difficulty, top_n=60):
    """
    Filter and copy top N data files for a given difficulty level.
    
    Args:
        difficulty: Difficulty level (5, 10, or 15)
        top_n: Number of top entries to copy (default: 60)
    """
    # Paths
    base_dir = Path(__file__).parent.parent
    csv_file = base_dir / 'complexity statistic' / f'complexity_statistics_{difficulty}_sorted.csv'
    source_dir = base_dir / 'data_en' / str(difficulty)
    target_dir = base_dir / 'data_en_filtered' / str(difficulty)
    
    # Check if CSV file exists
    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    # Read sorted CSV
    df = pd.read_csv(csv_file)
    
    # Get top N entries
    top_entries = df.head(top_n)
    
    print(f"\n{'='*80}")
    print(f"Processing Difficulty {difficulty}: Top {top_n} entries")
    print(f"{'='*80}")
    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")
    print(f"Total entries in CSV: {len(df)}")
    print(f"Copying top: {len(top_entries)}")
    print()
    
    total_files_success = 0
    total_files_failed = 0
    entries_processed = 0
    
    # Process each entry
    for idx, row in top_entries.iterrows():
        skeleton_filename = row['filename']
        composite_score = row['composite_score']
        
        entries_processed += 1
        print(f"[{entries_processed}/{len(top_entries)}] {skeleton_filename} (score: {composite_score})")
        
        success, failed = copy_data_files(skeleton_filename, source_dir, target_dir)
        total_files_success += success
        total_files_failed += failed
        
        if failed > 0:
            print(f"    ✓ Copied {success} files, ⚠️  {failed} failed/missing")
        else:
            print(f"    ✓ Copied {success} files")
    
    print()
    print(f"{'='*80}")
    print(f"Difficulty {difficulty} Summary:")
    print(f"  Entries processed: {entries_processed}")
    print(f"  Files copied successfully: {total_files_success}")
    print(f"  Files failed/missing: {total_files_failed}")
    print(f"{'='*80}")
    
    return True


def main():
    """Main function to filter and copy data for all difficulty levels."""
    print("=" * 80)
    print("Data Filtering Tool - Copy Top N Entries")
    print("=" * 80)
    print()
    print("This script will copy the top 60 entries from each difficulty level")
    print("based on the sorted complexity statistics.")
    print()
    
    # Configuration
    difficulty_levels = [5, 10, 15]
    top_n = 60
    
    # Create base target directory
    base_dir = Path(__file__).parent.parent
    target_base = base_dir / 'data_en_filtered'
    target_base.mkdir(exist_ok=True)
    
    print(f"Target base directory: {target_base}")
    print()
    
    # Process each difficulty level
    success_count = 0
    for difficulty in difficulty_levels:
        if filter_and_copy_top_n(difficulty, top_n):
            success_count += 1
    
    print()
    print("=" * 80)
    print("Overall Summary")
    print("=" * 80)
    print(f"Difficulty levels processed: {success_count}/{len(difficulty_levels)}")
    print()
    
    # Count files in target directories
    for difficulty in difficulty_levels:
        target_dir = target_base / str(difficulty)
        if target_dir.exists():
            for subdir in ['dag', 'sources', 'inits', 'full', 'narrative']:
                subdir_path = target_dir / subdir
                if subdir_path.exists():
                    file_count = len(list(subdir_path.glob('*.json')))
                    print(f"  data_en_filtered/{difficulty}/{subdir}/: {file_count} files")
    
    print()
    print("=" * 80)
    print("✅ Filtering and copying completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()