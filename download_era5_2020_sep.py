#!/usr/bin/env python3
"""
Download ERA5 data for September 1, 2020 for Aurora forecasting.
Requires CDS API credentials configured in ~/.cdsapirc
"""

import cdsapi
from pathlib import Path

# Configuration
download_path = Path("/content/drive/MyDrive/Research")
date_str = "2020-09-01"
year = "2020"
month = "09"
day = "01"

def main():
    print("=" * 70)
    print("ERA5 Data Download for September 1, 2020")
    print("=" * 70)
    print(f"Output directory: {download_path}")
    print("=" * 70)

    # Initialize CDS API client
    try:
        c = cdsapi.Client()
        print("✓ CDS API client initialized\n")
    except Exception as e:
        print(f"✗ Error initializing CDS API client: {e}")
        print("\nPlease ensure ~/.cdsapirc is configured with your CDS API credentials")
        print("Get your credentials from: https://cds.climate.copernicus.eu/")
        return

    download_path.mkdir(parents=True, exist_ok=True)

    # Download static variables (only if not already exists)
    static_file = download_path / "static.nc"
    if not static_file.exists():
        print("Downloading static variables...")
        try:
            c.retrieve(
                "reanalysis-era5-single-levels",
                {
                    "product_type": "reanalysis",
                    "variable": [
                        "geopotential",
                        "land_sea_mask",
                        "soil_type",
                    ],
                    "year": year,
                    "month": month,
                    "day": day,
                    "time": "00:00",
                    "format": "netcdf",
                },
                str(static_file),
            )
            print(f"✓ Static variables downloaded: {static_file}\n")
        except Exception as e:
            print(f"✗ Error downloading static variables: {e}\n")
    else:
        print(f"○ Static variables already exist: {static_file}\n")

    # Download surface-level variables
    surface_file = download_path / f"{date_str}-surface-level.nc"
    if not surface_file.exists():
        print("Downloading surface-level variables...")
        try:
            c.retrieve(
                "reanalysis-era5-single-levels",
                {
                    "product_type": "reanalysis",
                    "variable": [
                        "2m_temperature",
                        "10m_u_component_of_wind",
                        "10m_v_component_of_wind",
                        "mean_sea_level_pressure",
                    ],
                    "year": year,
                    "month": month,
                    "day": day,
                    "time": ["00:00", "06:00", "12:00", "18:00"],
                    "format": "netcdf",
                },
                str(surface_file),
            )
            print(f"✓ Surface-level variables downloaded: {surface_file}\n")
        except Exception as e:
            print(f"✗ Error downloading surface-level variables: {e}\n")
            return
    else:
        print(f"○ Surface-level variables already exist: {surface_file}\n")

    # Download atmospheric variables
    atmos_file = download_path / f"{date_str}-atmospheric.nc"
    if not atmos_file.exists():
        print("Downloading atmospheric variables...")
        try:
            c.retrieve(
                "reanalysis-era5-pressure-levels",
                {
                    "product_type": "reanalysis",
                    "variable": [
                        "temperature",
                        "u_component_of_wind",
                        "v_component_of_wind",
                        "specific_humidity",
                        "geopotential",
                    ],
                    "pressure_level": [
                        "50", "100", "150", "200", "250", "300",
                        "400", "500", "600", "700", "850", "925", "1000",
                    ],
                    "year": year,
                    "month": month,
                    "day": day,
                    "time": ["00:00", "06:00", "12:00", "18:00"],
                    "format": "netcdf",
                },
                str(atmos_file),
            )
            print(f"✓ Atmospheric variables downloaded: {atmos_file}\n")
        except Exception as e:
            print(f"✗ Error downloading atmospheric variables: {e}\n")
            return
    else:
        print(f"○ Atmospheric variables already exist: {atmos_file}\n")

    print("=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)
    print(f"ERA5 data for {date_str} is ready for Aurora forecasting!")
    print(f"Location: {download_path}")
    print("\nFiles created:")
    print(f"  - {static_file.name}")
    print(f"  - {surface_file.name}")
    print(f"  - {atmos_file.name}")
    print("=" * 70)


if __name__ == "__main__":
    main()
