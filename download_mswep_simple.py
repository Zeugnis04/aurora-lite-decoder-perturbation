#!/usr/bin/env python3
"""
Simple MSWEP 2022 downloader - copies files from Google Drive symlink to local directory.
This is faster than using rclone and works directly with the mounted Drive.
"""

import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm

# Configuration
SOURCE_DIR = Path("./MSWEP_V280/Past_nogauge/3hourly")  # From symlink
OUTPUT_DIR = Path("./MSWEP_local/2022")

# Date ranges to download for 2022
DOWNLOAD_PERIODS = [
    # Sample weeks from each season for testing
    ("2022-01-15", "2022-01-21", "January 2022 (Winter week)"),
    ("2022-04-15", "2022-04-21", "April 2022 (Spring week)"),
    ("2022-07-15", "2022-07-21", "July 2022 (Summer week)"),
    ("2022-10-15", "2022-10-21", "October 2022 (Fall week)"),
]

# Set to True to download full months instead of weeks
DOWNLOAD_FULL_MONTHS = False

# Set to True to download the entire year
DOWNLOAD_FULL_YEAR = False


def generate_mswep_filename(date, hour):
    """
    Generate MSWEP filename for a given date and hour.

    Format: YYYYDDD.HH
    - YYYY: year
    - DDD: day of year (001-366)
    - HH: hour (00, 03, 06, 09, 12, 15, 18, 21)
    """
    day_of_year = date.timetuple().tm_yday
    year = date.year
    filename = f"{year}{day_of_year:03d}.{hour:02d}"
    return filename


def copy_file(filename, source_dir, output_dir):
    """Copy a single MSWEP file from source to destination."""
    source = source_dir / filename
    dest = output_dir / filename

    # Skip if already exists
    if dest.exists():
        return "exists"

    # Check if source exists
    if not source.exists():
        return "not_found"

    try:
        shutil.copy2(source, dest)
        return "success"
    except Exception as e:
        return f"error: {e}"


def download_period(start_date, end_date, description, source_dir, output_dir):
    """Download MSWEP files for a date range."""
    print(f"\n{'='*70}")
    print(f"Downloading: {description}")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*70}\n")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate date range
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    hours = [0, 3, 6, 9, 12, 15, 18, 21]

    total_files = len(dates) * len(hours)
    stats = {"success": 0, "exists": 0, "not_found": 0, "error": 0}

    print(f"Total files to process: {total_files}\n")

    # Progress bar
    with tqdm(total=total_files, desc="Copying files") as pbar:
        for date in dates:
            for hour in hours:
                filename = generate_mswep_filename(date, hour)
                result = copy_file(filename, source_dir, output_dir)

                if result == "success":
                    stats["success"] += 1
                elif result == "exists":
                    stats["exists"] += 1
                elif result == "not_found":
                    stats["not_found"] += 1
                    tqdm.write(f"  ⚠ Not found: {filename}")
                else:
                    stats["error"] += 1
                    tqdm.write(f"  ✗ Error: {filename} - {result}")

                pbar.update(1)

    print(f"\n{'='*70}")
    print(f"Summary for {description}:")
    print(f"  Total files: {total_files}")
    print(f"  Copied: {stats['success']}")
    print(f"  Already existed: {stats['exists']}")
    print(f"  Not found: {stats['not_found']}")
    print(f"  Errors: {stats['error']}")
    print(f"{'='*70}\n")

    return stats


def main():
    print("="*70)
    print("MSWEP 2022 Data Download Script (Local Copy)")
    print("="*70)
    print(f"Source directory: {SOURCE_DIR.absolute()}")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print("="*70)

    # Check if source directory exists
    if not SOURCE_DIR.exists():
        print(f"\n✗ ERROR: Source directory not found: {SOURCE_DIR}")
        print("  Make sure the MSWEP_V280 symlink is set up correctly.")
        return

    print("✓ Source directory found\n")

    # Determine what to download
    if DOWNLOAD_FULL_YEAR:
        periods = [("2022-01-01", "2022-12-31", "Full Year 2022")]
    elif DOWNLOAD_FULL_MONTHS:
        periods = [
            ("2022-01-01", "2022-01-31", "January 2022"),
            ("2022-04-01", "2022-04-30", "April 2022"),
            ("2022-07-01", "2022-07-31", "July 2022"),
            ("2022-10-01", "2022-10-31", "October 2022"),
        ]
    else:
        periods = DOWNLOAD_PERIODS

    # Download each period
    total_stats = {"success": 0, "exists": 0, "not_found": 0, "error": 0}

    for start_date, end_date, description in periods:
        stats = download_period(start_date, end_date, description, SOURCE_DIR, OUTPUT_DIR)
        for key in total_stats:
            total_stats[key] += stats[key]

    # Overall summary
    print("\n" + "="*70)
    print("OVERALL SUMMARY")
    print("="*70)
    print(f"Total files copied: {total_stats['success']}")
    print(f"Already existed: {total_stats['exists']}")
    print(f"Not found: {total_stats['not_found']}")
    print(f"Errors: {total_stats['error']}")
    print(f"\nOutput directory: {OUTPUT_DIR.absolute()}")
    print("="*70)

    # Show directory contents
    if OUTPUT_DIR.exists():
        num_files = len(list(OUTPUT_DIR.glob("*")))
        print(f"\nFiles in output directory: {num_files}")

        # Calculate approximate size
        try:
            total_size = sum(f.stat().st_size for f in OUTPUT_DIR.glob("*"))
            size_mb = total_size / (1024 * 1024)
            print(f"Total size: {size_mb:.2f} MB")
        except:
            pass


if __name__ == "__main__":
    main()
