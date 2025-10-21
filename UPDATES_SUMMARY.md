# Updates Summary - Visualization Tools

## ✨ New Features Added

### 1. **Difference Plotting in Option A**

Three new functions added to `save_step_figures.py`:

#### `plot_difference_step()`
Creates a 2-panel figure showing precipitation and wind differences for one timestep
- **Input**: Difference arrays (perturbed - control)
- **Output**: Single figure with both variables
- **File naming**: `difference_step_XXX.png`

#### `save_all_differences()`
Saves difference figures for all timesteps
- **Input**: Both control and perturbed results
- **Calculates**: Differences automatically
- **Output**: One figure per timestep

#### `save_all_simulations()`
**ALL-IN-ONE convenience function** that saves everything:
- Control simulation figures → `base_dir/control/`
- Perturbed simulation figures → `base_dir/perturbed/`
- Difference figures → `base_dir/differences/`

**Usage:**
```python
from save_step_figures import save_all_simulations

saved_paths = save_all_simulations(
    control_results=control_results,
    perturbed_results=perturbed_results,
    base_output_dir='figures',
    region='full',
    dpi=150,
    save_differences=True,  # Set to False to skip differences
    precip_log_scale=False  # Set to True for log scale
)
```

---

### 2. **Logarithmic Scale for Precipitation**

Added `precip_log_scale` parameter to all plotting functions:

- When `True`: Uses logarithmic color scale for precipitation
- Useful for: Better visualization of both light and heavy precipitation
- Range: 0.1 mm to 50 mm (log scale)
- Zero values: Replaced with 0.1 mm to avoid log(0)

**Functions supporting log scale:**
- `plot_wind_and_precip_step()`
- `save_all_steps()`
- `save_all_simulations()`

**Example:**
```python
save_all_steps(
    results=control_results,
    output_dir='figures/control',
    prefix='control',
    region='full',
    precip_log_scale=True  # Enable log scale
)
```

---

### 3. **Updated Plot_Saved_Results.ipynb (Option B)**

#### Updated imports:
```python
sys.path.append('/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/')
from save_step_figures import (
    subset_north_america,
    setup_north_america_map,
    plot_wind_and_precip_step,
    plot_difference_step,        # NEW
    save_all_differences,        # NEW
    create_comparison_figure
)
```

#### New Section 6: Save All Difference Figures
```python
diff_dir = output_dir / 'differences'
save_all_differences(
    control_results=control_results,
    perturbed_results=perturbed_results,
    output_dir=diff_dir,
    region=REGION,
    dpi=150
)
```

#### Updated Section 7: Log Scale Option
Shows how to use `precip_log_scale=True` when saving figures

---

## 📁 File Organization

After running `save_all_simulations()`, your directory structure will be:

```
figures/
├── control/
│   ├── control_step_000.png
│   ├── control_step_001.png
│   └── ...
├── perturbed/
│   ├── perturbed_step_000.png
│   ├── perturbed_step_001.png
│   └── ...
└── differences/
    ├── difference_step_000.png
    ├── difference_step_001.png
    └── ...
```

---

## 🎨 Figure Types Summary

### 1. **Individual Simulation Figures** (2 panels)
- Left: Precipitation
- Right: 500 hPa Wind Speed
- Created by: `save_all_steps()`

### 2. **Difference Figures** (2 panels) **NEW**
- Left: Precipitation Difference (Perturbed - Control)
- Right: Wind Speed Difference (Perturbed - Control)
- Uses diverging colormap (RdBu_r)
- Created by: `save_all_differences()`

### 3. **Comparison Figures** (2×3 layout)
- Row 1: Precipitation (Control | Perturbed | Difference)
- Row 2: Wind Speed (Control | Perturbed | Difference)
- Created by: `create_comparison_figure()`

---

## 🚀 Quick Start Examples

### Example 1: Save everything with one command
```python
import sys
sys.path.append('/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/')
from save_step_figures import save_all_simulations

# After running your simulations...
saved_paths = save_all_simulations(
    control_results=control_results,
    perturbed_results=perturbed_results,
    base_output_dir='figures',
    region='us',  # Focus on US
    dpi=150,
    save_differences=True,
    precip_log_scale=False
)

print(f"Saved {len(saved_paths['control'])} control figures")
print(f"Saved {len(saved_paths['perturbed'])} perturbed figures")
print(f"Saved {len(saved_paths['differences'])} difference figures")
```

### Example 2: Save only differences
```python
from save_step_figures import save_all_differences

save_all_differences(
    control_results=control_results,
    perturbed_results=perturbed_results,
    output_dir='figures/differences',
    region='full',
    dpi=150
)
```

### Example 3: Use log scale for precipitation
```python
from save_step_figures import save_all_steps

save_all_steps(
    results=control_results,
    output_dir='figures/control_logscale',
    prefix='control',
    region='full',
    precip_log_scale=True  # Log scale
)
```

---

## 📊 When to Use Log Scale

**Use log scale when:**
- You have both light drizzle (< 1 mm) and heavy rain (> 20 mm)
- You want to see spatial patterns in light precipitation
- Comparing regions with very different precipitation amounts

**Use linear scale when:**
- Precipitation is relatively uniform (e.g., all < 10 mm)
- You want to emphasize differences in heavy precipitation
- Creating figures for general audiences

---

## 🔧 All Function Signatures

```python
# Individual plotting
plot_wind_and_precip_step(precip_data, wind_data, lat, lon, time_str,
                          step_num, output_dir, region='full',
                          prefix='control', dpi=150, precip_log_scale=False)

plot_difference_step(precip_diff, wind_diff, lat, lon, time_str,
                    step_num, output_dir, region='full', dpi=150)

# Batch plotting
save_all_steps(results, output_dir, prefix='control', region='full',
              dpi=150, precip_log_scale=False)

save_all_differences(control_results, perturbed_results, output_dir,
                    region='full', dpi=150)

save_all_simulations(control_results, perturbed_results, base_output_dir,
                    region='full', dpi=150, save_differences=True,
                    precip_log_scale=False)

create_comparison_figure(control_results, perturbed_results, step_num,
                        output_dir, region='full', dpi=150)
```

---

## 📝 Important Notes

### File Locations
All utility files are now in:
```
/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/
├── save_step_figures.py
├── export_simulation_data.py
├── add_to_perturbation_notebook.py
├── Plot_Saved_Results.ipynb
└── README_VISUALIZATION.md
```

### Import Path
Update your imports to:
```python
sys.path.append('/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/')
```

Or keep files in `/content/` and use:
```python
sys.path.append('/content')
```

### Color Scales
- **Precipitation**: Blues (linear) or Blues with LogNorm (log scale)
- **Wind Speed**: YlOrRd (yellow-orange-red)
- **Differences**: RdBu_r (red-blue diverging, red=positive, blue=negative)

---

## 🎯 Recommended Workflow

1. **Run simulation** in your perturbation notebook
2. **Quick check**: Use inline plotting (see `add_to_perturbation_notebook.py`)
3. **Save everything**:
   ```python
   save_all_simulations(control_results, perturbed_results,
                       'figures', save_differences=True)
   ```
4. **Export data** (optional for later analysis):
   ```python
   export_both_simulations(control_results, perturbed_results,
                          'exported_data')
   ```
5. **Create publication figures** using `Plot_Saved_Results.ipynb`

---

## 📈 Performance Tips

- **Differences only**: If you only need differences, use `save_all_differences()` directly
- **Regional subsets**: Use `region='us'` instead of `region='full'` to speed up plotting
- **Lower DPI**: Use `dpi=100` for quick previews, `dpi=150` for sharing, `dpi=300` for publications
- **Skip differences**: Set `save_differences=False` in `save_all_simulations()` if not needed

---

## 🆕 What Changed

**Files modified:**
- ✅ `save_step_figures.py` - Added 3 new functions + log scale support
- ✅ `Plot_Saved_Results.ipynb` - Added difference plotting section + updated imports
- ✅ `add_to_perturbation_notebook.py` - Added examples for new functions

**Backward compatible:** All existing code will still work!

---

Last updated: 2025-10-14
