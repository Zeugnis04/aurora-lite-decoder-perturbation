#!/usr/bin/env python3
"""
Generate all plots: control steps, perturbed steps, and comparison figures
"""

import sys
import numpy as np
from pathlib import Path

# Add project directory to path
sys.path.insert(0, '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation')

from export_simulation_data import load_results_from_npz
from save_step_figures import save_all_simulations

def load_data_with_fallback(npz_path):
    """
    Load data and handle both wind_speed_500 and wind_speed_700 keys
    """
    data = np.load(npz_path, allow_pickle=True)

    # Check which key exists
    if 'wind_speed_700' in data:
        wind_key = 'wind_speed_700'
    elif 'wind_speed_500' in data:
        wind_key = 'wind_speed_500'
        print(f"Note: Using old key 'wind_speed_500' from {npz_path.name}")
    else:
        raise ValueError(f"No wind speed data found in {npz_path}")

    results = {
        'precip': [data['precip'][i] for i in range(data['precip'].shape[0])],
        'wind_speed_700': [data[wind_key][i] for i in range(data[wind_key].shape[0])],
        'times': data['times'].tolist(),
        'lat': data['lat'],
        'lon': data['lon'],
    }

    # Load metadata if present
    if 'metadata' in data:
        results['metadata'] = eval(str(data['metadata']))

    print(f"✓ Loaded from: {npz_path}")
    print(f"  - Steps: {len(results['precip'])}")
    print(f"  - Grid: {results['lat'].shape[0]} x {results['lon'].shape[0]}")

    return results

def main():
    # Paths - using local copy for faster access
    data_dir = Path('/content/exported_data')
    base_output_dir = Path('/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/figures')

    control_path = data_dir / 'pacific_perturbation_control.npz'
    perturbed_path = data_dir / 'pacific_perturbation_perturbed.npz'

    # Load data
    print("="*70)
    print("LOADING DATA")
    print("="*70)
    print("\nLoading control simulation...")
    control_results = load_data_with_fallback(control_path)

    print("\nLoading perturbed simulation...")
    perturbed_results = load_data_with_fallback(perturbed_path)

    # Generate all figures
    print("\n" + "="*70)
    print("GENERATING ALL FIGURES")
    print("="*70)

    saved_paths = save_all_simulations(
        control_results=control_results,
        perturbed_results=perturbed_results,
        base_output_dir=base_output_dir,
        region='full',  # Options: 'full', 'us', 'east_us'
        dpi=150,
        save_differences=True
    )

    print("\n" + "="*70)
    print("✓ ALL FIGURES GENERATED SUCCESSFULLY!")
    print("="*70)
    print(f"\nOutput directory: {base_output_dir}")
    print(f"  - Control figures: {base_output_dir}/control/")
    print(f"  - Perturbed figures: {base_output_dir}/perturbed/")
    print(f"  - Comparison figures: {base_output_dir}/differences/")
    print(f"\nTotal files generated:")
    print(f"  - Control: {len(saved_paths['control'])} files")
    print(f"  - Perturbed: {len(saved_paths['perturbed'])} files")
    print(f"  - Differences: {len(saved_paths['differences'])} files")

if __name__ == "__main__":
    main()
