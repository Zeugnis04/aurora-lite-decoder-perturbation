#!/usr/bin/env python3
"""
Download MSWEP 2022 3-hourly precipitation data for evaluation.

This script downloads specific 2022 MSWEP files from Google Drive
for out-of-sample precipitation forecast evaluation.
"""

import subprocess
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Configuration
OUTPUT_DIR = Path("./MSWEP_local/2022")
GOOGLE_DRIVE_BASE = "GoogleDrive:/MSWEP_V280/Past_nogauge/3hourly"

# Date ranges to download (adjust as needed)
# Let's download a few representative months from 2022
DOWNLOAD_PERIODS = [
    # Winter: January 2022
    ("2022-01-01", "2022-01-31", "January 2022 (Winter)"),
    # Spring: April 2022
    ("2022-04-01", "2022-04-30", "April 2022 (Spring)"),
    # Summer: July 2022
    ("2022-07-01", "2022-07-31", "July 2022 (Summer)"),
    # Fall: October 2022
    ("2022-10-01", "2022-10-31", "October 2022 (Fall)"),
]

# Or download the entire year (warning: large!)
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


def download_file(filename, output_dir):
    """Download a single MSWEP file using rclone."""
    source = f"{GOOGLE_DRIVE_BASE}/{filename}"
    dest = output_dir / filename

    # Skip if already exists
    if dest.exists():
        print(f"  ✓ Already exists: {filename}")
        return True

    # Run rclone command
    cmd = [
        "rclone", "copy", "-v",
        "--drive-shared-with-me",
        source,
        str(output_dir)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"  ✓ Downloaded: {filename}")
            return True
        else:
            print(f"  ✗ Failed: {filename}")
            print(f"    Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout: {filename}")
        return False
    except Exception as e:
        print(f"  ✗ Error downloading {filename}: {e}")
        return False


def download_period(start_date, end_date, description):
    """Download MSWEP files for a date range."""
    print(f"\n{'='*60}")
    print(f"Downloading: {description}")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*60}\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate date range
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    hours = [0, 3, 6, 9, 12, 15, 18, 21]

    total_files = len(dates) * len(hours)
    downloaded = 0
    failed = 0

    print(f"Total files to download: {total_files}\n")

    for date in dates:
        print(f"Processing {date.strftime('%Y-%m-%d')} (day {date.timetuple().tm_yday})...")
        for hour in hours:
            filename = generate_mswep_filename(date, hour)
            if download_file(filename, OUTPUT_DIR):
                downloaded += 1
            else:
                failed += 1

    print(f"\n{'='*60}")
    print(f"Summary for {description}:")
    print(f"  Total: {total_files}")
    print(f"  Downloaded: {downloaded}")
    print(f"  Failed: {failed}")
    print(f"{'='*60}\n")

    return downloaded, failed


def download_full_year_2022():
    """Download all 2022 MSWEP files."""
    return download_period("2022-01-01", "2022-12-31", "Full Year 2022")


def main():
    print("MSWEP 2022 Data Download Script")
    print("="*60)
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print(f"Google Drive source: {GOOGLE_DRIVE_BASE}")
    print("="*60)

    # Check if rclone is available
    try:
        subprocess.run(["rclone", "version"], capture_output=True, check=True)
        print("✓ rclone is installed\n")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ rclone is not installed or not in PATH")
        print("  Please install rclone first: https://rclone.org/downloads/")
        return

    total_downloaded = 0
    total_failed = 0

    if DOWNLOAD_FULL_YEAR:
        # Download entire year
        downloaded, failed = download_full_year_2022()
        total_downloaded += downloaded
        total_failed += failed
    else:
        # Download selected periods
        for start_date, end_date, description in DOWNLOAD_PERIODS:
            downloaded, failed = download_period(start_date, end_date, description)
            total_downloaded += downloaded
            total_failed += failed

    print("\n" + "="*60)
    print("OVERALL SUMMARY")
    print("="*60)
    print(f"Total files downloaded: {total_downloaded}")
    print(f"Total failures: {total_failed}")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print("="*60)

    # Show directory size
    if OUTPUT_DIR.exists():
        num_files = len(list(OUTPUT_DIR.glob("*")))
        print(f"\nFiles in output directory: {num_files}")


if __name__ == "__main__":
    main()
