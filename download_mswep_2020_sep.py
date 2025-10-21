#!/usr/bin/env python3
"""
Download MSWEP data for September 1, 2020 for testing.
"""

import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from tqdm import tqdm

# Configuration
SOURCE_DIR = Path("./MSWEP_V280/Past/3hourly")  # From symlink
OUTPUT_DIR = Path("./MSWEP_local/2020")

# Download September 1-5, 2020 (5 days for forecasting + evaluation)
START_DATE = "2020-09-01"
END_DATE = "2020-09-05"


def generate_mswep_filename(date, hour):
    """
    Generate MSWEP filename for a given date and hour.

    Format: YYYYDDD.HH.nc
    - YYYY: year
    - DDD: day of year (001-366)
    - HH: hour (00, 03, 06, 09, 12, 15, 18, 21)
    """
    day_of_year = date.timetuple().tm_yday
    year = date.year
    filename = f"{year}{day_of_year:03d}.{hour:02d}.nc"
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


def main():
    print("="*70)
    print(f"MSWEP September 1-5, 2020 Data Download")
    print("="*70)
    print(f"Source directory: {SOURCE_DIR.absolute()}")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print(f"Date range: {START_DATE} to {END_DATE}")
    print("="*70)

    # Check if source directory exists
    if not SOURCE_DIR.exists():
        print(f"\n✗ ERROR: Source directory not found: {SOURCE_DIR}")
        print("  Make sure the MSWEP_V280 symlink is set up correctly.")
        return

    print("✓ Source directory found\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate date range
    dates = pd.date_range(start=START_DATE, end=END_DATE, freq='D')
    hours = [0, 3, 6, 9, 12, 15, 18, 21]

    stats = {"success": 0, "exists": 0, "not_found": 0, "error": 0}

    print(f"Downloading {len(dates)} days x {len(hours)} hours = {len(dates) * len(hours)} files\n")

    for date in dates:
        print(f"\n{date.strftime('%Y-%m-%d')} (Day {date.timetuple().tm_yday} of {date.year}):")
        for hour in hours:
            filename = generate_mswep_filename(date, hour)
            result = copy_file(filename, SOURCE_DIR, OUTPUT_DIR)

            if result == "success":
                stats["success"] += 1
                print(f"  ✓ {filename}")
            elif result == "exists":
                stats["exists"] += 1
                print(f"  ○ {filename}")
            elif result == "not_found":
                stats["not_found"] += 1
                print(f"  ✗ {filename} (not found)")
            else:
                stats["error"] += 1
                print(f"  ✗ {filename} - {result}")

    print(f"\n{'='*70}")
    print(f"Summary:")
    print(f"  Total files: {len(dates) * len(hours)}")
    print(f"  Copied: {stats['success']}")
    print(f"  Already existed: {stats['exists']}")
    print(f"  Not found: {stats['not_found']}")
    print(f"  Errors: {stats['error']}")
    print(f"{'='*70}\n")

    if stats['success'] + stats['exists'] == len(dates) * len(hours):
        print(f"✓ MSWEP data ready for {START_DATE} to {END_DATE}")
        print(f"  Location: {OUTPUT_DIR.absolute()}")
    else:
        print(f"⚠ Some files could not be downloaded")


if __name__ == "__main__":
    main()
