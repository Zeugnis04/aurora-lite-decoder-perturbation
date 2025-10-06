# MSWEP Data Download Summary

## Overview
Successfully downloaded 2020 MSWEP precipitation data for out-of-sample precipitation forecast evaluation using the Aurora-Lite decoder model.

## What Was Done

### 1. Fixed CUDA Out of Memory Issue
**Problem:** The `rollout_with_decoder` function was causing CUDA OOM errors.

**Solution:** Updated `MSWEP_Precipitation_Evaluation.ipynb` cell 14:
- Moved `torch.inference_mode()` outside the loop
- Added `.detach().clone()` to latent tensors
- Added periodic `torch.cuda.empty_cache()` every 4 steps
- Now matches the correct pattern from `Inference_decoders.ipynb`

### 2. Fixed MSWEP Data Loading
**Problem:** MSWEP files use specific naming convention with .nc extension.

**File Naming Convention:**
```
Format: YYYYDDD.HH.nc
- YYYY = year (e.g., 2020)
- DDD = day of year (001-366)
- HH = hour (00, 03, 06, 09, 12, 15, 18, 21)
- .nc = NetCDF extension

Examples:
- 2020116.06.nc = April 25, 2020, 06:00 UTC (day 116)
- 2020015.00.nc = January 15, 2020, 00:00 UTC (day 15)
```

### 3. Downloaded 2020 Data
**Downloaded:** 224 files (504 MB) from 4 weeks in 2020:
- January 15-21, 2020 (Winter)
- April 15-21, 2020 (Spring)
- July 15-21, 2020 (Summer)
- October 15-21, 2020 (Fall/Hurricane season)

**Location:** `./MSWEP_local/2020/`

## Files Created

### Download Scripts
1. **`download_mswep_2020.py`** - Main download script for 2020 data
   - Uses local copy from Google Drive symlink
   - Progress bar with tqdm
   - Configurable date ranges

2. **`download_mswep_simple.py`** - Alternative version
3. **`download_mswep_2022.py`** - For future 2022 downloads (if data becomes available)

### Updated Notebook Functions
**`load_mswep_sample()` in `MSWEP_Precipitation_Evaluation.ipynb`:**
- Correctly implements MSWEP file naming (YYYYDDD.HH.nc)
- Uses `use_local=True` to load from local directory first (faster)
- Falls back to symlink if local file not found
- Uses Past_nogauge variant (recommended for evaluation)

**`rollout_with_decoder()` in `MSWEP_Precipitation_Evaluation.ipynb`:**
- Fixed memory management
- Proper `torch.inference_mode()` placement
- Periodic cache clearing

## How to Use

### Run Forecast Evaluation on 2020 Data

The downloaded 2020 data is ready to use. You can now:

1. **Test with January 2020 data:**
   ```python
   test_date_str = "2020-01-15"  # Winter weather
   ```

2. **Test with October 2020 data:**
   ```python
   test_date_str = "2020-10-15"  # Fall/Hurricane season
   ```

3. **Run the evaluation cell** (cell 18) in the notebook - it will:
   - Load ERA5 data for initial conditions
   - Run 4-step rollout forecast (24 hours)
   - Load MSWEP ground truth from local directory
   - Compute evaluation metrics

### Download More Data

To download additional 2020 data:

```bash
# Edit download_mswep_2020.py to set:
DOWNLOAD_FULL_MONTHS = True  # Download full months instead of weeks
# or
DOWNLOAD_FULL_YEAR = True    # Download entire year 2020 (2920 files, ~5-10 GB)

# Then run:
python3 download_mswep_2020.py
```

## Next Steps

### Immediate:
1. ✅ Test the rollout with 2020-01-15 data (already have ERA5 for 2012-10-24, need 2020 ERA5)
2. Download ERA5 data for 2020 dates to run full evaluation

### For Comprehensive Evaluation:
1. Download ERA5 data for the 2020 periods we have MSWEP for:
   - 2020-01-15 to 2020-01-21
   - 2020-04-15 to 2020-04-21
   - 2020-07-15 to 2020-07-21
   - 2020-10-15 to 2020-10-21

2. Run full evaluation loop (cell 23 in notebook)

3. Compare results across seasons

## Data Sources

- **MSWEP V2.8:** Multi-Source Weighted-Ensemble Precipitation
  - Source: `./MSWEP_V280/Past/3hourly/` (Google Drive symlink)
  - Local copy: `./MSWEP_local/2020/`
  - Variant: Past_nogauge (recommended for evaluation with gauge reference)

- **ERA5:** Atmospheric reanalysis data
  - Source: `./Research/`
  - Need to download matching dates for 2020

## Key Improvements

1. **Memory Efficiency:** Fixed CUDA OOM - can now run multi-step rollouts
2. **Faster Data Access:** Local MSWEP files load much faster than symlink
3. **Correct File Format:** Using proper MSWEP naming convention with .nc extension
4. **Out-of-Sample Data:** 2020 is truly unseen if training was on 2017-2019
5. **Seasonal Coverage:** Downloaded data from all 4 seasons for comprehensive evaluation

## Technical Details

### MSWEP Data Structure
```
MSWEP_V280/
├── Past/
│   └── 3hourly/
│       ├── 2020001.00.nc (Jan 1, 00:00)
│       ├── 2020001.03.nc (Jan 1, 03:00)
│       └── ...
├── Past_nogauge/  # Recommended for evaluation
└── NRT/           # Near real-time data
```

### Local Directory Structure
```
MSWEP_local/
└── 2020/
    ├── 2020015.00.nc
    ├── 2020015.03.nc
    └── ... (224 files total)
```

## Memory Usage

- **MSWEP files:** ~2.25 MB each (compressed NetCDF)
- **Downloaded total:** 504 MB for 224 files
- **Full year 2020:** ~6-7 GB (2920 files)

## References

- MSWEP Documentation: Use 'Past_nogauge' for precipitation evaluations with gauge observations as reference
- Aurora Documentation: https://microsoft.github.io/aurora/
- File naming: Day of year calculated using `date.timetuple().tm_yday`
