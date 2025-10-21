"""
Export simulation results to files for later analysis and plotting.
"""

import numpy as np
from pathlib import Path
import pickle
import json


def export_results_to_npz(results, output_path, metadata=None):
    """
    Export simulation results to a compressed .npz file.

    Args:
        results: Dictionary with 'precip', 'wind_speed_700', 'times', 'lat', 'lon'
        output_path: Path to save .npz file
        metadata: Optional dict with additional metadata (e.g., perturbation params)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Stack lists into 3D arrays
    precip_array = np.stack(results['precip'], axis=0)  # Shape: (steps, lat, lon)
    wind_array = np.stack(results['wind_speed_700'], axis=0)  # Shape: (steps, lat, lon)
    times_array = np.array(results['times'])

    # Prepare data dict
    save_dict = {
        'precip': precip_array,
        'wind_speed_700': wind_array,
        'times': times_array.astype('datetime64[ns]'),
        'lat': results['lat'],
        'lon': results['lon'],
    }

    # Add metadata if provided
    if metadata:
        save_dict['metadata'] = json.dumps(metadata)

    # Save
    np.savez_compressed(output_path, **save_dict)
    print(f"✓ Exported to: {output_path}")
    print(f"  - Precip shape: {precip_array.shape}")
    print(f"  - Wind shape: {wind_array.shape}")
    print(f"  - Time steps: {len(times_array)}")

    return str(output_path)


def load_results_from_npz(npz_path):
    """
    Load simulation results from .npz file.

    Args:
        npz_path: Path to .npz file

    Returns:
        Dictionary with 'precip', 'wind_speed_700', 'times', 'lat', 'lon', 'metadata'
    """
    data = np.load(npz_path, allow_pickle=True)

    results = {
        'precip': [data['precip'][i] for i in range(data['precip'].shape[0])],
        'wind_speed_700': [data['wind_speed_700'][i] for i in range(data['wind_speed_700'].shape[0])],
        'times': data['times'].tolist(),
        'lat': data['lat'],
        'lon': data['lon'],
    }

    # Load metadata if present
    if 'metadata' in data:
        results['metadata'] = json.loads(str(data['metadata']))

    print(f"✓ Loaded from: {npz_path}")
    print(f"  - Steps: {len(results['precip'])}")
    print(f"  - Grid: {results['lat'].shape[0]} x {results['lon'].shape[0]}")

    return results


def export_both_simulations(control_results, perturbed_results, output_dir,
                            perturbation_params=None, experiment_name="pacific_perturbation"):
    """
    Export both control and perturbed simulation results.

    Args:
        control_results: Dictionary from control simulation
        perturbed_results: Dictionary from perturbed simulation
        output_dir: Directory to save files
        perturbation_params: Dict with perturbation parameters
        experiment_name: Name for this experiment

    Returns:
        Tuple of (control_path, perturbed_path)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare metadata
    control_metadata = {
        'experiment': experiment_name,
        'simulation_type': 'control',
        'n_steps': len(control_results['precip']),
    }

    perturbed_metadata = {
        'experiment': experiment_name,
        'simulation_type': 'perturbed',
        'n_steps': len(perturbed_results['precip']),
    }

    if perturbation_params:
        perturbed_metadata['perturbation'] = perturbation_params

    # Export control
    control_path = output_dir / f"{experiment_name}_control.npz"
    export_results_to_npz(control_results, control_path, control_metadata)

    # Export perturbed
    perturbed_path = output_dir / f"{experiment_name}_perturbed.npz"
    export_results_to_npz(perturbed_results, perturbed_path, perturbed_metadata)

    # Also save a summary JSON
    summary = {
        'experiment_name': experiment_name,
        'control_file': str(control_path.name),
        'perturbed_file': str(perturbed_path.name),
        'n_steps': len(control_results['precip']),
        'start_time': str(control_results['times'][0]),
        'end_time': str(control_results['times'][-1]),
        'grid_shape': {
            'lat': int(control_results['lat'].shape[0]),
            'lon': int(control_results['lon'].shape[0]),
        },
        'perturbation_params': perturbation_params,
    }

    summary_path = output_dir / f"{experiment_name}_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n✓ Summary saved to: {summary_path}")

    return str(control_path), str(perturbed_path)


def export_subset_region(results, output_path, region='us'):
    """
    Export a regional subset of the data (smaller file size).

    Args:
        results: Full simulation results
        output_path: Path to save subset
        region: 'full', 'us', 'east_us', or tuple (lat_min, lat_max, lon_min, lon_max)
    """
    from save_step_figures import subset_north_america

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lat = results['lat']
    lon = results['lon']

    # Subset each step
    precip_subset_list = []
    wind_subset_list = []

    for precip, wind in zip(results['precip'], results['wind_speed_700']):
        precip_sub, lat_sub, lon_sub, _ = subset_north_america(precip, lat, lon, region)
        wind_sub, _, _, _ = subset_north_america(wind, lat, lon, region)

        precip_subset_list.append(precip_sub)
        wind_subset_list.append(wind_sub)

    # Stack
    precip_array = np.stack(precip_subset_list, axis=0)
    wind_array = np.stack(wind_subset_list, axis=0)

    # Save
    np.savez_compressed(
        output_path,
        precip=precip_array,
        wind_speed_700=wind_array,
        times=np.array(results['times']).astype('datetime64[ns]'),
        lat=lat_sub,
        lon=lon_sub,
        region=region,
    )

    print(f"✓ Regional subset exported to: {output_path}")
    print(f"  - Region: {region}")
    print(f"  - Shape: {precip_array.shape}")

    return str(output_path)
