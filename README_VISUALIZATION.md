# Visualization Guide: North America Weather Perturbation Analysis

This guide explains how to visualize 500 hPa wind speed and precipitation over North America from your perturbation experiments.

## 📁 Files Created

1. **`save_step_figures.py`** - Functions to save figures during/after simulation
2. **`export_simulation_data.py`** - Export data to .npz files for later analysis
3. **`Plot_Saved_Results.ipynb`** - Standalone notebook for plotting exported data
4. **`add_to_perturbation_notebook.py`** - Code snippets to add to your existing notebook

## 🎯 Two Approaches

### **Option A: Save Figures Immediately After Simulation**

**Pros:** Simple, creates publication-ready figures right away
**Cons:** Slower, creates many files, less flexible

**Usage in your notebook:**

```python
# After running both simulations...
import sys
sys.path.append('/content')
from save_step_figures import save_all_steps, create_comparison_figure

# Save all timesteps for control simulation
save_all_steps(
    results=control_results,
    output_dir='figures/control_steps',
    prefix='control',
    region='full',  # or 'us', 'east_us'
    dpi=150
)

# Save all timesteps for perturbed simulation
save_all_steps(
    results=perturbed_results,
    output_dir='figures/perturbed_steps',
    prefix='perturbed',
    region='full',
    dpi=150
)

# Create comparison figures for selected steps
for step in [0, 7, 14, 21, 27]:
    create_comparison_figure(
        control_results=control_results,
        perturbed_results=perturbed_results,
        step_num=step,
        output_dir='figures/comparisons',
        region='full',
        dpi=150
    )
```

---

### **Option B: Export Data + Plot Later (RECOMMENDED)**

**Pros:** Fast export, flexible plotting, can replot without re-running simulation
**Cons:** Two-step process

#### Step 1: Export data (add to your simulation notebook)

```python
import sys
sys.path.append('/content')
from export_simulation_data import export_both_simulations

# After running both simulations...
perturbation_params = {
    'location': {'lat': PERTURB_LAT, 'lon': PERTURB_LON},
    'amplitude': amplitude,
    'sigma': sigma,
    'pressure_levels': f'{PERTURB_LEVELS_MIN}-{PERTURB_LEVELS_MAX} hPa',
}

export_both_simulations(
    control_results=control_results,
    perturbed_results=perturbed_results,
    output_dir='exported_data',
    perturbation_params=perturbation_params,
    experiment_name='pacific_perturbation'
)
```

This creates:
- `pacific_perturbation_control.npz` (~200-500 MB)
- `pacific_perturbation_perturbed.npz` (~200-500 MB)
- `pacific_perturbation_summary.json` (metadata)

#### Step 2: Plot in separate notebook

Use the provided **`Plot_Saved_Results.ipynb`** notebook, which includes:

✅ Load exported data
✅ Plot individual timesteps
✅ Create comparison plots (control vs perturbed vs difference)
✅ Time series analysis of differences
✅ Save publication-ready figures

---

## 🗺️ Region Options

When plotting, you can choose which region to focus on:

| Region      | Coverage                    | Lat Range | Lon Range (0-360°) | Lon Range (±180°) |
|-------------|-----------------------------|-----------|--------------------|-------------------|
| `'full'`    | All of North America        | 10-75°N   | 190-295°E          | -170 to -65°W     |
| `'us'`      | Continental United States   | 24-50°N   | 235-295°E          | -125 to -65°W     |
| `'east_us'` | Eastern United States       | 25-50°N   | 275-295°E          | -85 to -65°W      |
| Custom      | `(lat_min, lat_max, lon_min, lon_max)` | - | - | - |

**Example custom region:**
```python
# Pacific Northwest
region = (40, 55, 235, 250)  # 40-55°N, -125 to -110°W
```

---

## 📊 Variables Available

### 1. **Precipitation**
- Units: **meters** (in raw data), convert to **mm** by multiplying by 1000
- Temporal resolution: 6-hour accumulation
- Visualization: 'Blues' colormap, 0-50 mm range

### 2. **500 hPa Wind Speed**
- Units: **m/s**
- Computed as: √(u² + v²)
- Visualization: 'YlOrRd' colormap, 0-80 m/s range

### 3. **Differences (Perturbed - Control)**
- Both variables
- Visualization: 'RdBu_r' diverging colormap

---

## 🎨 Figure Types

### 1. **Individual Step Figures**
Two panels showing precipitation and wind for one timestep
- File: `control_step_014.png`, `perturbed_step_014.png`
- Size: ~2-3 MB each

### 2. **Comparison Figures** (2×3 layout)
Shows control, perturbed, and difference for both variables
- Top row: Precipitation (control | perturbed | difference)
- Bottom row: 500 hPa wind (control | perturbed | difference)
- File: `comparison_step_014.png`
- Size: ~4-5 MB each

### 3. **Time Series Plots**
Evolution of differences over forecast period
- Mean Absolute Error (MAE)
- Root Mean Square Error (RMSE)
- For both precipitation and wind

---

## 💡 Quick Inline Plotting

If you just want a quick look at one timestep without saving files, add this to your notebook:

```python
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

STEP = 14  # Choose step number

# Extract data
lat = control_results['lat']
lon = control_results['lon']
precip_diff = (perturbed_results['precip'][STEP] - control_results['precip'][STEP]) * 1000  # mm
wind_diff = perturbed_results['wind_speed_500'][STEP] - control_results['wind_speed_500'][STEP]

# Subset for North America (190-295°E, 10-75°N)
lat_mask = (lat >= 10) & (lat <= 75)
lon_mask = (lon >= 190) & (lon <= 295)
lat_idx, lon_idx = np.where(lat_mask)[0], np.where(lon_mask)[0]
precip_diff_sub = precip_diff[np.ix_(lat_idx, lon_idx)]
wind_diff_sub = wind_diff[np.ix_(lat_idx, lon_idx)]

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6),
                                subplot_kw={'projection': ccrs.PlateCarree()})

# Precipitation difference
ax1.set_extent([190, 295, 10, 75]); ax1.coastlines()
lon_grid, lat_grid = np.meshgrid(lon[lon_idx], lat[lat_idx])
max_p = max(abs(precip_diff_sub.min()), abs(precip_diff_sub.max()))
cf1 = ax1.contourf(lon_grid, lat_grid, precip_diff_sub,
                   levels=np.linspace(-max_p, max_p, 21), cmap='RdBu_r')
plt.colorbar(cf1, ax=ax1, label='Precip Diff (mm)')
ax1.set_title(f'Precipitation Difference - Step {STEP}', fontweight='bold')

# Wind difference
ax2.set_extent([190, 295, 10, 75]); ax2.coastlines()
max_w = max(abs(wind_diff_sub.min()), abs(wind_diff_sub.max()))
cf2 = ax2.contourf(lon_grid, lat_grid, wind_diff_sub,
                   levels=np.linspace(-max_w, max_w, 21), cmap='RdBu_r')
plt.colorbar(cf2, ax=ax2, label='Wind Diff (m/s)')
ax2.set_title(f'500 hPa Wind Difference - Step {STEP}', fontweight='bold')

plt.tight_layout(); plt.show()
```

---

## 📦 Data File Structure

### NPZ file contents:
```python
data = np.load('pacific_perturbation_control.npz')
print(data.files)  # ['precip', 'wind_speed_500', 'times', 'lat', 'lon', 'metadata']

# Arrays shapes:
# precip:         (n_steps, n_lat, n_lon)  - typically (28, 721, 1440)
# wind_speed_500: (n_steps, n_lat, n_lon)
# times:          (n_steps,)               - numpy.datetime64
# lat:            (n_lat,)
# lon:            (n_lon,)
# metadata:       string (JSON)
```

### Loading data:
```python
from export_simulation_data import load_results_from_npz

results = load_results_from_npz('pacific_perturbation_control.npz')
# Returns dict with lists instead of arrays for easier iteration
```

---

## 🚀 Recommended Workflow

1. **Run your simulation** in `Pacific_Perturbation_Precipitation.ipynb`

2. **Export data immediately** (takes ~30 seconds):
   ```python
   from export_simulation_data import export_both_simulations
   export_both_simulations(control_results, perturbed_results,
                          output_dir='exported_data',
                          experiment_name='pacific_perturbation')
   ```

3. **Do initial quick checks** with inline plotting (see above)

4. **Later, create publication figures** using `Plot_Saved_Results.ipynb`:
   - Load data
   - Explore different timesteps
   - Adjust regions
   - Create comparison figures
   - Generate time series plots
   - Export high-resolution figures

---

## 🎯 Example Use Cases

### Case 1: Create figures for a paper
```python
# In Plot_Saved_Results.ipynb
steps = [0, 7, 14, 21]  # Days 0, 1.75, 3.5, 5.25
for step in steps:
    create_comparison_figure(
        control_results, perturbed_results,
        step_num=step, output_dir='figures/paper',
        region='us', dpi=300  # High resolution
    )
```

### Case 2: Focus on Eastern US
```python
# Export regional subset (smaller files)
from export_simulation_data import export_subset_region
export_subset_region(control_results, 'east_us_control.npz', region='east_us')
export_subset_region(perturbed_results, 'east_us_perturbed.npz', region='east_us')
```

### Case 3: Animate all timesteps
```python
# Save all frames
save_all_steps(control_results, 'animation/frames', prefix='ctrl', region='us')

# Then use ffmpeg or imageio to create animation:
# ffmpeg -framerate 5 -i ctrl_step_%03d.png -c:v libx264 animation.mp4
```

---

## ⚙️ Customization

### Change color scales:
Edit `save_step_figures.py`:
```python
# For precipitation (line ~95)
levels=np.arange(0, 100, 5),  # 0-100 mm instead of 0-50

# For wind (line ~110)
levels=np.arange(0, 120, 10),  # 0-120 m/s instead of 0-80
```

### Add wind vectors:
```python
# In your plotting code, after getting u and v components:
u_500 = pred_batch.atmos_vars["u"][0, -1, idx_500].cpu().numpy()
v_500 = pred_batch.atmos_vars["v"][0, -1, idx_500].cpu().numpy()

# Subset for region
u_sub = u_500[np.ix_(lat_idx, lon_idx)]
v_sub = v_500[np.ix_(lat_idx, lon_idx)]

# Plot vectors
ax.quiver(lon_grid[::10, ::10], lat_grid[::10, ::10],
          u_sub[::10, ::10], v_sub[::10, ::10],
          transform=ccrs.PlateCarree(), alpha=0.7)
```

---

## 📝 Notes

- Longitude convention: **0-360°** (not -180 to 180)
  - 190°E = 170°W
  - 295°E = 65°W

- Time resolution: **6 hours per step**
  - Step 0 = initial time
  - Step 7 = +42 hours = 1.75 days
  - Step 28 = +168 hours = 7 days

- Memory: Each full dataset (~28 steps, global) ≈ 400 MB compressed

---

## 🐛 Troubleshooting

**ImportError: No module named 'cartopy'**
```bash
pip install cartopy
```

**Figures are blank or wrong region**
- Check longitude range (must be 0-360 for North America: 190-295)
- Verify lat/lon arrays with `print(lat.min(), lat.max())`

**Files are huge**
- Use regional subsets with `export_subset_region()`
- Reduce DPI: `dpi=100` instead of `dpi=150`

**Plotting is slow**
- Load regional subset instead of full data
- Plot every Nth step instead of all steps

---

## 📚 Additional Resources

- Cartopy documentation: https://scitools.org.uk/cartopy/
- Aurora model paper: https://arxiv.org/abs/2405.13063
- ERA5 pressure levels: https://confluence.ecmwf.int/display/CKB/ERA5

---

**Questions?** Check the docstrings in the Python files or the example cells in `Plot_Saved_Results.ipynb`.
