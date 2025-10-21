"""
Functions to save figures for 700 hPa wind and precipitation over North America at each timestep.
"""

import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path


def setup_north_america_map(ax, extent=None):
    """
    Setup a map projection for North America.

    Args:
        ax: matplotlib axis with cartopy projection
        extent: [lon_min, lon_max, lat_min, lat_max] or None for default
    """
    if extent is None:
        # Default: Cover most of North America
        extent = [190, 295, 10, 75]  # 190-295°E = -170°W to -65°W, 10-75°N

    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle=':')
    ax.add_feature(cfeature.STATES, linewidth=0.3, edgecolor='gray')
    ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.3)

    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False

    return ax


def subset_north_america(data, lat, lon, region='full'):
    """
    Subset data for North America region.

    Args:
        data: 2D numpy array (lat, lon)
        lat: 1D latitude array
        lon: 1D longitude array (0-360 convention)
        region: 'full', 'us', 'east_us', or custom tuple (lat_min, lat_max, lon_min, lon_max)

    Returns:
        data_subset, lat_subset, lon_subset, extent (for plotting)
    """
    if region == 'full':
        # Full North America
        lat_range = (10, 75)
        lon_range = (190, 295)
    elif region == 'us':
        # Continental US
        lat_range = (24, 50)
        lon_range = (235, 295)
    elif region == 'east_us':
        # Eastern US
        lat_range = (25, 50)
        lon_range = (275, 295)
    elif isinstance(region, tuple) and len(region) == 4:
        lat_range = (region[0], region[1])
        lon_range = (region[2], region[3])
    else:
        raise ValueError(f"Unknown region: {region}")

    # Create masks
    lat_mask = (lat >= lat_range[0]) & (lat <= lat_range[1])
    lon_mask = (lon >= lon_range[0]) & (lon <= lon_range[1])

    # Get indices
    lat_idx = np.where(lat_mask)[0]
    lon_idx = np.where(lon_mask)[0]

    # Subset data
    data_subset = data[np.ix_(lat_idx, lon_idx)]
    lat_subset = lat[lat_idx]
    lon_subset = lon[lon_idx]

    # Extent for cartopy (lon_min, lon_max, lat_min, lat_max)
    extent = [lon_range[0], lon_range[1], lat_range[0], lat_range[1]]

    return data_subset, lat_subset, lon_subset, extent


def plot_wind_and_precip_step(
    precip_data,
    wind_data,
    lat,
    lon,
    time_str,
    step_num,
    output_dir,
    region='full',
    prefix='control',
    dpi=200,
    precip_log_scale=False
):
    """
    Create and save a figure with 700 hPa wind and precipitation for one timestep.

    Args:
        precip_data: 2D array of precipitation (meters)
        wind_data: 2D array of wind speed at 700 hPa (m/s)
        lat: 1D latitude array
        lon: 1D longitude array (0-360)
        time_str: String representation of the forecast time
        step_num: Step number (for filename)
        output_dir: Directory to save figures
        region: Region to plot ('full', 'us', 'east_us', or tuple)
        prefix: Prefix for filename (e.g., 'control', 'perturbed')
        dpi: Resolution for saved figures
        precip_log_scale: If True, use logarithmic scale for precipitation
    """
    from matplotlib.colors import LogNorm

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Subset data for North America
    precip_subset, lat_sub, lon_sub, extent = subset_north_america(precip_data, lat, lon, region)
    wind_subset, _, _, _ = subset_north_america(wind_data, lat, lon, region)

    # Convert precipitation to mm
    precip_mm = precip_subset * 1000

    # Create figure with two subplots
    fig = plt.figure(figsize=(16, 6))

    # Plot 1: Precipitation
    ax1 = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
    setup_north_america_map(ax1, extent)

    lon_grid, lat_grid = np.meshgrid(lon_sub, lat_sub)

    # Set up levels and normalization for precipitation
    if precip_log_scale:
        # Use log scale - set minimum to avoid log(0)
        precip_plot = np.maximum(precip_mm, 0.1)
        cf1 = ax1.contourf(
            lon_grid, lat_grid, precip_plot,
            levels=np.logspace(-1, np.log10(50), 5),
            cmap='Blues',
            norm=LogNorm(vmin=0.1, vmax=50),
            extend='max',
            transform=ccrs.PlateCarree()
        )
        label = '6-hour Precipitation (mm, log scale)'
    else:
        cf1 = ax1.contourf(
            lon_grid, lat_grid, precip_mm,
            levels=np.arange(0, 50.5, 5),
            cmap='Blues',
            extend='max',
            transform=ccrs.PlateCarree()
        )
        label = '6-hour Precipitation (mm)'

    plt.colorbar(cf1, ax=ax1, label=label, shrink=0.8)
    ax1.set_title(f'Precipitation - Step {step_num}\n{time_str}', fontsize=12, fontweight='bold')

    # Plot 2: 700 hPa Wind Speed
    ax2 = fig.add_subplot(1, 2, 2, projection=ccrs.PlateCarree())
    setup_north_america_map(ax2, extent)

    cf2 = ax2.contourf(
        lon_grid, lat_grid, wind_subset,
        levels=np.linspace(15, 30, 5),  # 15-30 m/s with fine gradation
        cmap='rainbow',
        extend='both',
        transform=ccrs.PlateCarree()
    )
    plt.colorbar(cf2, ax=ax2, label='Wind Speed (m/s)', shrink=0.8)
    ax2.set_title(f'700 hPa Wind Speed - Step {step_num}\n{time_str}', fontsize=12, fontweight='bold')

    plt.tight_layout()

    # Save figure
    filename = f"{prefix}_step_{step_num:03d}.png"
    filepath = output_dir / filename
    plt.savefig(filepath, dpi=dpi, bbox_inches='tight')
    plt.close()

    return str(filepath)


def save_all_steps(results, output_dir, prefix='control', region='full', dpi=200, precip_log_scale=False):
    """
    Save figures for all timesteps from simulation results.

    Args:
        results: Dictionary with 'precip', 'wind_speed_700', 'times', 'lat', 'lon'
        output_dir: Directory to save figures
        prefix: Prefix for filenames
        region: Region to plot
        dpi: Resolution
        precip_log_scale: If True, use logarithmic scale for precipitation

    Returns:
        List of saved file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    lat = results['lat']
    lon = results['lon']
    saved_files = []

    print(f"\nSaving figures to: {output_dir}")
    print(f"Total steps: {len(results['precip'])}")

    for step_num, (precip, wind, time) in enumerate(
        zip(results['precip'], results['wind_speed_700'], results['times'])
    ):
        time_str = str(time)

        filepath = plot_wind_and_precip_step(
            precip_data=precip,
            wind_data=wind,
            lat=lat,
            lon=lon,
            time_str=time_str,
            step_num=step_num,
            output_dir=output_dir,
            region=region,
            prefix=prefix,
            dpi=dpi,
            precip_log_scale=precip_log_scale
        )

        saved_files.append(filepath)

        if (step_num + 1) % 5 == 0:
            print(f"  Saved step {step_num + 1}/{len(results['precip'])}")

    print(f"✓ All figures saved! Total: {len(saved_files)} files")
    return saved_files


def create_comparison_figure(
    control_results,
    perturbed_results,
    step_num,
    output_dir,
    region='full',
    dpi=200
):
    """
    Create a comparison figure showing control vs perturbed and their difference.

    Args:
        control_results: Dictionary from control simulation
        perturbed_results: Dictionary from perturbed simulation
        step_num: Which timestep to plot
        output_dir: Directory to save figure
        region: Region to plot
        dpi: Resolution
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    lat = control_results['lat']
    lon = control_results['lon']

    # Get data for this step
    precip_control = control_results['precip'][step_num]
    precip_perturbed = perturbed_results['precip'][step_num]
    wind_control = control_results['wind_speed_700'][step_num]
    wind_perturbed = perturbed_results['wind_speed_700'][step_num]
    time_str = str(control_results['times'][step_num])

    # Subset for region
    precip_ctrl_sub, lat_sub, lon_sub, extent = subset_north_america(precip_control, lat, lon, region)
    precip_pert_sub, _, _, _ = subset_north_america(precip_perturbed, lat, lon, region)
    wind_ctrl_sub, _, _, _ = subset_north_america(wind_control, lat, lon, region)
    wind_pert_sub, _, _, _ = subset_north_america(wind_perturbed, lat, lon, region)

    # Convert to mm
    precip_ctrl_mm = precip_ctrl_sub * 1000
    precip_pert_mm = precip_pert_sub * 1000
    precip_diff_mm = precip_pert_mm - precip_ctrl_mm
    wind_diff = wind_pert_sub - wind_ctrl_sub

    # Create 2x3 figure
    fig = plt.figure(figsize=(18, 12))
    lon_grid, lat_grid = np.meshgrid(lon_sub, lat_sub)

    # Row 1: Precipitation
    # Control
    ax1 = fig.add_subplot(2, 3, 1, projection=ccrs.PlateCarree())
    setup_north_america_map(ax1, extent)
    cf1 = ax1.contourf(lon_grid, lat_grid, precip_ctrl_mm, levels=np.arange(0, 50.5, 5),
                       cmap='Blues', extend='max', transform=ccrs.PlateCarree())
    plt.colorbar(cf1, ax=ax1, label='Precip (mm)', shrink=0.8)
    ax1.set_title(f'Control - Precipitation\nStep {step_num}', fontsize=11, fontweight='bold')

    # Perturbed
    ax2 = fig.add_subplot(2, 3, 2, projection=ccrs.PlateCarree())
    setup_north_america_map(ax2, extent)
    cf2 = ax2.contourf(lon_grid, lat_grid, precip_pert_mm, levels=np.arange(0, 50.5, 5),
                       cmap='Blues', extend='max', transform=ccrs.PlateCarree())
    plt.colorbar(cf2, ax=ax2, label='Precip (mm)', shrink=0.8)
    ax2.set_title(f'Perturbed - Precipitation\nStep {step_num}', fontsize=11, fontweight='bold')

    # Difference
    ax3 = fig.add_subplot(2, 3, 3, projection=ccrs.PlateCarree())
    setup_north_america_map(ax3, extent)
    max_diff = max(abs(precip_diff_mm.min()), abs(precip_diff_mm.max()))
    levels_diff = np.linspace(-max_diff, max_diff, 5)
    cf3 = ax3.contourf(lon_grid, lat_grid, precip_diff_mm, levels=levels_diff,
                       cmap='RdBu_r', extend='both', transform=ccrs.PlateCarree())
    plt.colorbar(cf3, ax=ax3, label='Diff (mm)', shrink=0.8)
    ax3.set_title(f'Difference (Pert - Ctrl)\nPrecipitation', fontsize=11, fontweight='bold')

    # Row 2: Wind Speed at 700 hPa
    # Control
    ax4 = fig.add_subplot(2, 3, 4, projection=ccrs.PlateCarree())
    setup_north_america_map(ax4, extent)
    cf4 = ax4.contourf(lon_grid, lat_grid, wind_ctrl_sub, levels=np.linspace(15, 30, 5),
                       cmap='rainbow', extend='both', transform=ccrs.PlateCarree())
    plt.colorbar(cf4, ax=ax4, label='Wind (m/s)', shrink=0.8)
    ax4.set_title(f'Control - 700 hPa Wind\nStep {step_num}', fontsize=11, fontweight='bold')

    # Perturbed
    ax5 = fig.add_subplot(2, 3, 5, projection=ccrs.PlateCarree())
    setup_north_america_map(ax5, extent)
    cf5 = ax5.contourf(lon_grid, lat_grid, wind_pert_sub, levels=np.linspace(15, 30, 5),
                       cmap='rainbow', extend='both', transform=ccrs.PlateCarree())
    plt.colorbar(cf5, ax=ax5, label='Wind (m/s)', shrink=0.8)
    ax5.set_title(f'Perturbed - 700 hPa Wind\nStep {step_num}', fontsize=11, fontweight='bold')

    # Difference
    ax6 = fig.add_subplot(2, 3, 6, projection=ccrs.PlateCarree())
    setup_north_america_map(ax6, extent)
    max_diff_wind = max(abs(wind_diff.min()), abs(wind_diff.max()))
    levels_diff_wind = np.linspace(-max_diff_wind, max_diff_wind, 5)
    cf6 = ax6.contourf(lon_grid, lat_grid, wind_diff, levels=levels_diff_wind,
                       cmap='RdBu_r', extend='both', transform=ccrs.PlateCarree())
    plt.colorbar(cf6, ax=ax6, label='Diff (m/s)', shrink=0.8)
    ax6.set_title(f'Difference (Pert - Ctrl)\n700 hPa Wind', fontsize=11, fontweight='bold')

    fig.suptitle(f'Comparison at Step {step_num} - {time_str}', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()

    # Save
    filename = f"comparison_step_{step_num:03d}.png"
    filepath = output_dir / filename
    plt.savefig(filepath, dpi=dpi, bbox_inches='tight')
    plt.close()

    print(f"Saved comparison figure: {filepath}")
    return str(filepath)


def plot_difference_step(
    precip_diff,
    wind_diff,
    lat,
    lon,
    time_str,
    step_num,
    output_dir,
    region='full',
    dpi=200,
    precip_max_diff=None,
    wind_max_diff=None
):
    """
    Create and save a figure showing differences (perturbed - control) for one timestep.

    Args:
        precip_diff: 2D array of precipitation difference (meters)
        wind_diff: 2D array of wind speed difference at 700 hPa (m/s)
        lat: 1D latitude array
        lon: 1D longitude array (0-360)
        time_str: String representation of the forecast time
        step_num: Step number (for filename)
        output_dir: Directory to save figures
        region: Region to plot ('full', 'us', 'east_us', or tuple)
        dpi: Resolution for saved figures
        precip_max_diff: Optional fixed max difference for precipitation (meters)
        wind_max_diff: Optional fixed max difference for wind (m/s)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Subset data for North America
    precip_diff_sub, lat_sub, lon_sub, extent = subset_north_america(precip_diff, lat, lon, region)
    wind_diff_sub, _, _, _ = subset_north_america(wind_diff, lat, lon, region)

    # Convert precipitation to mm
    precip_diff_mm = precip_diff_sub * 1000

    # Create figure with two subplots
    fig = plt.figure(figsize=(16, 6))
    lon_grid, lat_grid = np.meshgrid(lon_sub, lat_sub)

    # Plot 1: Precipitation Difference
    ax1 = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
    setup_north_america_map(ax1, extent)

    # Use provided max_diff or calculate from data
    if precip_max_diff is not None:
        max_diff_precip = precip_max_diff * 1000  # Convert to mm
    else:
        max_diff_precip = max(abs(precip_diff_mm.min()), abs(precip_diff_mm.max()))

    if max_diff_precip > 0:
        levels_precip = np.linspace(-max_diff_precip, max_diff_precip, 5)
    else:
        levels_precip = np.linspace(-1, 1, 5)

    cf1 = ax1.contourf(
        lon_grid, lat_grid, precip_diff_mm,
        levels=levels_precip,
        cmap='RdBu_r',
        extend='both',
        transform=ccrs.PlateCarree()
    )
    plt.colorbar(cf1, ax=ax1, label='Precipitation Difference (mm)', shrink=0.8)
    ax1.set_title(f'Precipitation Difference (Pert - Ctrl)\nStep {step_num}: {time_str}',
                  fontsize=12, fontweight='bold')

    # Plot 2: Wind Speed Difference
    ax2 = fig.add_subplot(1, 2, 2, projection=ccrs.PlateCarree())
    setup_north_america_map(ax2, extent)

    # Use provided max_diff or calculate from data
    if wind_max_diff is not None:
        max_diff_wind = wind_max_diff
    else:
        max_diff_wind = max(abs(wind_diff_sub.min()), abs(wind_diff_sub.max()))

    if max_diff_wind > 0:
        levels_wind = np.linspace(-max_diff_wind, max_diff_wind, 5)
    else:
        levels_wind = np.linspace(-1, 1, 5)

    cf2 = ax2.contourf(
        lon_grid, lat_grid, wind_diff_sub,
        levels=levels_wind,
        cmap='RdBu_r',
        extend='both',
        transform=ccrs.PlateCarree()
    )
    plt.colorbar(cf2, ax=ax2, label='Wind Speed Difference (m/s)', shrink=0.8)
    ax2.set_title(f'700 hPa Wind Difference (Pert - Ctrl)\nStep {step_num}: {time_str}',
                  fontsize=12, fontweight='bold')

    plt.tight_layout()

    # Save figure
    filename = f"difference_step_{step_num:03d}.png"
    filepath = output_dir / filename
    plt.savefig(filepath, dpi=dpi, bbox_inches='tight')
    plt.close()

    return str(filepath)


def save_all_differences(control_results, perturbed_results, output_dir,
                        region='full', dpi=200):
    """
    Save difference figures (perturbed - control) for all timesteps.
    Uses 95th percentile for consistent scaling across all steps.

    Args:
        control_results: Dictionary from control simulation
        perturbed_results: Dictionary from perturbed simulation
        output_dir: Directory to save figures
        region: Region to plot
        dpi: Resolution

    Returns:
        List of saved file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    lat = control_results['lat']
    lon = control_results['lon']
    saved_files = []

    print(f"\nSaving difference figures to: {output_dir}")
    print(f"Total steps: {len(control_results['precip'])}")

    # First pass: Calculate all differences to find 95th percentile for consistent scaling
    print("Calculating 95th percentile for consistent scaling...")
    all_precip_diffs = []
    all_wind_diffs = []

    for step_num in range(len(control_results['precip'])):
        precip_diff = perturbed_results['precip'][step_num] - control_results['precip'][step_num]
        wind_diff = perturbed_results['wind_speed_700'][step_num] - control_results['wind_speed_700'][step_num]

        # Subset for region to match what will be plotted
        from save_step_figures import subset_north_america
        precip_diff_sub, _, _, _ = subset_north_america(precip_diff, lat, lon, region)
        wind_diff_sub, _, _, _ = subset_north_america(wind_diff, lat, lon, region)

        all_precip_diffs.append(precip_diff_sub)
        all_wind_diffs.append(wind_diff_sub)

    # Calculate 95th percentile for max/min
    all_precip_diffs_flat = np.concatenate([d.flatten() for d in all_precip_diffs])
    all_wind_diffs_flat = np.concatenate([d.flatten() for d in all_wind_diffs])

    precip_max_diff = np.percentile(np.abs(all_precip_diffs_flat), 99)
    wind_max_diff = np.percentile(np.abs(all_wind_diffs_flat), 99)

    print(f"  Precipitation 95th percentile: ±{precip_max_diff*1000:.2f} mm")
    print(f"  Wind 95th percentile: ±{wind_max_diff:.2f} m/s")

    # Second pass: Plot with consistent scaling
    for step_num in range(len(control_results['precip'])):
        # Calculate differences
        precip_diff = perturbed_results['precip'][step_num] - control_results['precip'][step_num]
        wind_diff = perturbed_results['wind_speed_700'][step_num] - control_results['wind_speed_700'][step_num]
        time_str = str(control_results['times'][step_num])

        filepath = plot_difference_step(
            precip_diff=precip_diff,
            wind_diff=wind_diff,
            lat=lat,
            lon=lon,
            time_str=time_str,
            step_num=step_num,
            output_dir=output_dir,
            region=region,
            dpi=dpi,
            precip_max_diff=precip_max_diff,
            wind_max_diff=wind_max_diff
        )

        saved_files.append(filepath)

        if (step_num + 1) % 5 == 0:
            print(f"  Saved step {step_num + 1}/{len(control_results['precip'])}")

    print(f"✓ All difference figures saved! Total: {len(saved_files)} files")
    return saved_files


def save_all_simulations(control_results, perturbed_results, base_output_dir,
                        region='full', dpi=200, save_differences=True, precip_log_scale=False):
    """
    Convenience function to save control, perturbed, and difference figures.

    Args:
        control_results: Dictionary from control simulation
        perturbed_results: Dictionary from perturbed simulation
        base_output_dir: Base directory for all figures
        region: Region to plot
        dpi: Resolution
        save_differences: Whether to also save difference plots
        precip_log_scale: If True, use logarithmic scale for precipitation

    Returns:
        Dictionary with lists of saved file paths for each type
    """
    base_output_dir = Path(base_output_dir)

    saved_paths = {}

    # Save control simulation
    print("\n" + "="*70)
    print("SAVING CONTROL SIMULATION FIGURES")
    print("="*70)
    control_dir = base_output_dir / 'control'
    saved_paths['control'] = save_all_steps(
        control_results, control_dir, prefix='control', region=region, dpi=dpi, precip_log_scale=precip_log_scale
    )

    # Save perturbed simulation
    print("\n" + "="*70)
    print("SAVING PERTURBED SIMULATION FIGURES")
    print("="*70)
    perturbed_dir = base_output_dir / 'perturbed'
    saved_paths['perturbed'] = save_all_steps(
        perturbed_results, perturbed_dir, prefix='perturbed', region=region, dpi=dpi, precip_log_scale=precip_log_scale
    )

    # Save differences
    if save_differences:
        print("\n" + "="*70)
        print("SAVING DIFFERENCE FIGURES")
        print("="*70)
        diff_dir = base_output_dir / 'differences'
        saved_paths['differences'] = save_all_differences(
            control_results, perturbed_results, diff_dir, region=region, dpi=dpi
        )

    print("\n" + "="*70)
    print("✓ ALL FIGURES SAVED SUCCESSFULLY!")
    print("="*70)
    print(f"Output directory: {base_output_dir}")
    print(f"Total control figures: {len(saved_paths['control'])}")
    print(f"Total perturbed figures: {len(saved_paths['perturbed'])}")
    if save_differences:
        print(f"Total difference figures: {len(saved_paths['differences'])}")

    return saved_paths
