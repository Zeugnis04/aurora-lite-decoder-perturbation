#!/usr/bin/env python3
"""
Test script to check if data can be loaded and regenerate figures with new settings.
"""

import sys
import numpy as np
from pathlib import Path

# Add project directory to path
sys.path.insert(0, '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation')

print("="*70)
print("TESTING DATA LOADING AND FIGURE GENERATION")
print("="*70)

# Test 1: Try to load NPZ files directly from Google Drive
print("\n1. Testing direct load from Google Drive...")
try:
    data_path = '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/exported_data/pacific_perturbation_control.npz'

    # Try different approaches
    print("   Attempting numpy load...")
    data = np.load(data_path, allow_pickle=True)
    print("   ✓ SUCCESS! Data loaded.")
    print(f"   Keys: {list(data.keys())}")

    # Check if it has old or new wind key
    if 'wind_speed_700' in data:
        print("   ✓ Data has 'wind_speed_700' key (new format)")
        can_plot = True
    elif 'wind_speed_500' in data:
        print("   ⚠ Data has 'wind_speed_500' key (old format)")
        print("   → Need to re-run simulation with 700 hPa extraction")
        can_plot = False
    else:
        print("   ✗ No wind speed data found")
        can_plot = False

except Exception as e:
    print(f"   ✗ FAILED: {type(e).__name__}: {str(e)[:100]}")
    can_plot = False

# Test 2: Check if we can import the plotting functions
print("\n2. Testing import of updated plotting functions...")
try:
    from save_step_figures import (
        save_all_simulations,
        plot_wind_and_precip_step,
        save_all_differences
    )
    print("   ✓ Successfully imported plotting functions with new settings")
    print("   → 700 hPa wind: 15-30 m/s, rainbow colormap")
    print("   → Differences: 95th percentile scaling")
except Exception as e:
    print(f"   ✗ Import failed: {e}")

# Test 3: Summary and next steps
print("\n" + "="*70)
print("SUMMARY & NEXT STEPS")
print("="*70)

if can_plot:
    print("\n✓ Data can be loaded and has correct format!")
    print("\nTo regenerate figures with new settings, run:")
    print("  python generate_all_plots.py")
    print("\nOr in your notebook, add this cell:")
    print("""
    from save_step_figures import save_all_simulations

    saved_paths = save_all_simulations(
        control_results=control_results,
        perturbed_results=perturbed_results,
        base_output_dir='figures',
        region='full',
        dpi=150,
        save_differences=True
    )
    """)
else:
    print("\n⚠ Cannot regenerate figures yet. You need to:")
    print("\n1. Open your Pacific_Perturbation_Precipitation.ipynb notebook")
    print("\n2. Update wind extraction to use 700 hPa:")
    print("   Find where you calculate wind speed and change:")
    print("   ")
    print("   # OLD:")
    print("   idx_500 = list(p_levels).index(500)")
    print("   u_500 = preds_org.atmos_vars['u'][0, -1, idx_500].cpu().numpy()")
    print("   v_500 = preds_org.atmos_vars['v'][0, -1, idx_500].cpu().numpy()")
    print("   wind_speed = np.sqrt(u_500**2 + v_500**2)")
    print("   ")
    print("   # NEW:")
    print("   idx_700 = list(p_levels).index(700)")
    print("   u_700 = preds_org.atmos_vars['u'][0, -1, idx_700].cpu().numpy()")
    print("   v_700 = preds_org.atmos_vars['v'][0, -1, idx_700].cpu().numpy()")
    print("   wind_speed = np.sqrt(u_700**2 + v_700**2)")
    print("   ")
    print("3. Store with new key:")
    print("   control_results['wind_speed_700'].append(wind_speed)")
    print("   ")
    print("4. After running simulations, use:")
    print("   from save_step_figures import save_all_simulations")
    print("   saved_paths = save_all_simulations(...)")

print("\n" + "="*70)
