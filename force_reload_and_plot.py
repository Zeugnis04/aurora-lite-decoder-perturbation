#!/usr/bin/env python3
"""
Force reload the save_step_figures module and print diagnostic info.
Add this to your notebook BEFORE calling save_all_simulations.
"""

import sys
import importlib

# Remove any cached imports
if 'save_step_figures' in sys.modules:
    del sys.modules['save_step_figures']

# Ensure path
if '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation' not in sys.path:
    sys.path.insert(0, '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation')

# Fresh import
import save_step_figures

# Verify settings
import inspect
source = inspect.getsource(save_step_figures.plot_wind_and_precip_step)

print("="*70)
print("MODULE RELOAD VERIFICATION")
print("="*70)

print("\nChecking plot_wind_and_precip_step function:")
if 'rainbow' in source:
    print("  ✓ Colormap: rainbow")
else:
    print("  ✗ Colormap: NOT rainbow")

if 'linspace(15, 30' in source:
    print("  ✓ Wind range: 15-30 m/s")
elif 'arange(0, 80' in source:
    print("  ✗ Wind range: 0-80 m/s (OLD)")
else:
    print("  ? Wind range: Unknown")

source2 = inspect.getsource(save_step_figures.save_all_differences)
if 'percentile' in source2:
    print("  ✓ Difference scaling: 95th percentile")
else:
    print("  ✗ Difference scaling: NOT using percentile")

print("\n" + "="*70)
print("If all checks pass, proceed with:")
print("  saved_paths = save_step_figures.save_all_simulations(...)")
print("="*70)
