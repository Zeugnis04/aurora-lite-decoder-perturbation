"""
Code snippets to add to your Pacific_Perturbation_Precipitation.ipynb notebook.

Add these cells AFTER running both simulations.
"""

# ============================================================================
# OPTION A: Save figures during/after simulation
# ============================================================================

# Cell 1: Import the plotting utilities
"""
import sys
sys.path.append('/content')
from save_step_figures import save_all_steps, create_comparison_figure
"""

# Cell 2: Save figures for all control steps
"""
# Save all control simulation steps
control_fig_dir = '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/figures/control_steps'
save_all_steps(
    results=control_results,
    output_dir=control_fig_dir,
    prefix='control',
    region='full',  # Options: 'full', 'us', 'east_us'
    dpi=150
)
"""

# Cell 3: Save figures for all perturbed steps
"""
# Save all perturbed simulation steps
perturbed_fig_dir = '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/figures/perturbed_steps'
save_all_steps(
    results=perturbed_results,
    output_dir=perturbed_fig_dir,
    prefix='perturbed',
    region='full',
    dpi=150
)
"""

# Cell 4: Save difference plots for all steps
"""
# Save all difference (perturbed - control) figures
from save_step_figures import save_all_differences

diff_dir = '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/figures/differences'
save_all_differences(
    control_results=control_results,
    perturbed_results=perturbed_results,
    output_dir=diff_dir,
    region='full',
    dpi=150
)
"""

# Cell 5: Create comparison figures for selected steps
"""
# Create comparison figures for key timesteps
comparison_dir = '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/figures/comparisons'
steps_to_compare = [0, 7, 14, 21, 27]  # Days 0, 1.75, 3.5, 5.25, 6.75

for step in steps_to_compare:
    if step < len(control_results['precip']):
        create_comparison_figure(
            control_results=control_results,
            perturbed_results=perturbed_results,
            step_num=step,
            output_dir=comparison_dir,
            region='full',
            dpi=150
        )

print(f"✓ Created {len(steps_to_compare)} comparison figures")
"""

# Cell 6: ALL-IN-ONE - Save everything with one command
"""
# Save control, perturbed, AND difference figures all at once!
from save_step_figures import save_all_simulations

base_dir = '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/figures'
saved_paths = save_all_simulations(
    control_results=control_results,
    perturbed_results=perturbed_results,
    base_output_dir=base_dir,
    region='full',
    dpi=150,
    save_differences=True  # Set to False if you only want control & perturbed
)

print(f"\\n✓ All figures saved!")
print(f"  Control: {base_dir}/control/")
print(f"  Perturbed: {base_dir}/perturbed/")
print(f"  Differences: {base_dir}/differences/")
"""


# ============================================================================
# OPTION B: Export data for later plotting
# ============================================================================

# Cell 1: Import export utilities
"""
import sys
sys.path.append('/content')
from export_simulation_data import export_both_simulations, export_subset_region
"""

# Cell 2: Export both simulations (full data)
"""
# Export full simulation data
data_dir = '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/exported_data'

# Define perturbation parameters for metadata
perturbation_params = {
    'location': {
        'lat': PERTURB_LAT,
        'lon': PERTURB_LON,
    },
    'amplitude': amplitude,
    'sigma': sigma,
    'pressure_levels': f'{PERTURB_LEVELS_MIN}-{PERTURB_LEVELS_MAX} hPa',
    'pattern': 'gaussian',
}

# Export both simulations
control_path, perturbed_path = export_both_simulations(
    control_results=control_results,
    perturbed_results=perturbed_results,
    output_dir=data_dir,
    perturbation_params=perturbation_params,
    experiment_name='pacific_perturbation'
)

print(f"\\n✓ Data exported successfully!")
print(f"  Control: {control_path}")
print(f"  Perturbed: {perturbed_path}")
"""

# Cell 3: Export regional subsets (smaller files, faster to work with)
"""
# Export US-only subset for faster plotting
us_data_dir = '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/exported_data/us_subset'

export_subset_region(
    results=control_results,
    output_path=f'{us_data_dir}/control_us.npz',
    region='us'
)

export_subset_region(
    results=perturbed_results,
    output_path=f'{us_data_dir}/perturbed_us.npz',
    region='us'
)

print("\\n✓ US subset exported!")
"""


# ============================================================================
# OPTION C: Quick plot of a single step (add inline to notebook)
# ============================================================================

# Cell: Quick visualization of one timestep
"""
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

# Choose step to plot
STEP = 14  # Step 14 = 3.5 days

# Get data
lat = control_results['lat']
lon = control_results['lon']
precip_ctrl = control_results['precip'][STEP] * 1000  # Convert to mm
precip_pert = perturbed_results['precip'][STEP] * 1000
wind_ctrl = control_results['wind_speed_700'][STEP]
wind_pert = perturbed_results['wind_speed_700'][STEP]
time_str = str(control_results['times'][STEP])

# Subset for North America (190-295°E = -170 to -65°W, 10-75°N)
lat_mask = (lat >= 10) & (lat <= 75)
lon_mask = (lon >= 190) & (lon <= 295)
lat_idx = np.where(lat_mask)[0]
lon_idx = np.where(lon_mask)[0]

lat_sub = lat[lat_idx]
lon_sub = lon[lon_idx]
precip_ctrl_sub = precip_ctrl[np.ix_(lat_idx, lon_idx)]
precip_pert_sub = precip_pert[np.ix_(lat_idx, lon_idx)]
wind_ctrl_sub = wind_ctrl[np.ix_(lat_idx, lon_idx)]
wind_pert_sub = wind_pert[np.ix_(lat_idx, lon_idx)]

# Calculate differences
precip_diff = precip_pert_sub - precip_ctrl_sub
wind_diff = wind_pert_sub - wind_ctrl_sub

# Create figure
fig = plt.figure(figsize=(18, 12))
lon_grid, lat_grid = np.meshgrid(lon_sub, lat_sub)
extent = [190, 295, 10, 75]

# Row 1: Precipitation
ax1 = fig.add_subplot(2, 3, 1, projection=ccrs.PlateCarree())
ax1.set_extent(extent, crs=ccrs.PlateCarree())
ax1.coastlines(); ax1.add_feature(cfeature.BORDERS, linestyle=':')
cf1 = ax1.contourf(lon_grid, lat_grid, precip_ctrl_sub,
                   levels=np.arange(0, 50, 2.5), cmap='Blues', extend='max')
plt.colorbar(cf1, ax=ax1, label='mm')
ax1.set_title(f'Control Precip - Step {STEP}', fontweight='bold')

ax2 = fig.add_subplot(2, 3, 2, projection=ccrs.PlateCarree())
ax2.set_extent(extent, crs=ccrs.PlateCarree())
ax2.coastlines(); ax2.add_feature(cfeature.BORDERS, linestyle=':')
cf2 = ax2.contourf(lon_grid, lat_grid, precip_pert_sub,
                   levels=np.arange(0, 50, 2.5), cmap='Blues', extend='max')
plt.colorbar(cf2, ax=ax2, label='mm')
ax2.set_title(f'Perturbed Precip - Step {STEP}', fontweight='bold')

ax3 = fig.add_subplot(2, 3, 3, projection=ccrs.PlateCarree())
ax3.set_extent(extent, crs=ccrs.PlateCarree())
ax3.coastlines(); ax3.add_feature(cfeature.BORDERS, linestyle=':')
max_d = max(abs(precip_diff.min()), abs(precip_diff.max()))
cf3 = ax3.contourf(lon_grid, lat_grid, precip_diff,
                   levels=np.linspace(-max_d, max_d, 21), cmap='RdBu_r', extend='both')
plt.colorbar(cf3, ax=ax3, label='mm')
ax3.set_title('Precip Diff (Pert-Ctrl)', fontweight='bold')

# Row 2: Wind
ax4 = fig.add_subplot(2, 3, 4, projection=ccrs.PlateCarree())
ax4.set_extent(extent, crs=ccrs.PlateCarree())
ax4.coastlines(); ax4.add_feature(cfeature.BORDERS, linestyle=':')
cf4 = ax4.contourf(lon_grid, lat_grid, wind_ctrl_sub,
                   levels=np.arange(0, 80, 5), cmap='YlOrRd', extend='max')
plt.colorbar(cf4, ax=ax4, label='m/s')
ax4.set_title(f'Control 700hPa Wind - Step {STEP}', fontweight='bold')

ax5 = fig.add_subplot(2, 3, 5, projection=ccrs.PlateCarree())
ax5.set_extent(extent, crs=ccrs.PlateCarree())
ax5.coastlines(); ax5.add_feature(cfeature.BORDERS, linestyle=':')
cf5 = ax5.contourf(lon_grid, lat_grid, wind_pert_sub,
                   levels=np.arange(0, 80, 5), cmap='YlOrRd', extend='max')
plt.colorbar(cf5, ax=ax5, label='m/s')
ax5.set_title(f'Perturbed 700hPa Wind - Step {STEP}', fontweight='bold')

ax6 = fig.add_subplot(2, 3, 6, projection=ccrs.PlateCarree())
ax6.set_extent(extent, crs=ccrs.PlateCarree())
ax6.coastlines(); ax6.add_feature(cfeature.BORDERS, linestyle=':')
max_dw = max(abs(wind_diff.min()), abs(wind_diff.max()))
cf6 = ax6.contourf(lon_grid, lat_grid, wind_diff,
                   levels=np.linspace(-max_dw, max_dw, 21), cmap='RdBu_r', extend='both')
plt.colorbar(cf6, ax=ax6, label='m/s')
ax6.set_title('Wind Diff (Pert-Ctrl)', fontweight='bold')

fig.suptitle(f'North America - {time_str}', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()

# Print stats
print(f"\\nStep {STEP} Statistics:")
print(f"Precipitation difference: {precip_diff.mean():.2f} ± {precip_diff.std():.2f} mm")
print(f"Wind speed difference: {wind_diff.mean():.2f} ± {wind_diff.std():.2f} m/s")
"""
