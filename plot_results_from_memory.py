"""
Use this in your notebook after running simulations to generate all plots.

Add this cell to your notebook after you have control_results and perturbed_results:

```python
# Import plotting functions
from save_step_figures import save_all_simulations

# Generate all figures
base_output_dir = '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/figures'

saved_paths = save_all_simulations(
    control_results=control_results,
    perturbed_results=perturbed_results,
    base_output_dir=base_output_dir,
    region='full',  # Options: 'full', 'us', 'east_us'
    dpi=150,
    save_differences=True
)

print(f"\\n✓ All figures saved!")
print(f"  Control: {base_output_dir}/control/")
print(f"  Perturbed: {base_output_dir}/perturbed/")
print(f"  Differences: {base_output_dir}/differences/")
```

IMPORTANT: Make sure your control_results and perturbed_results dictionaries have:
- 'precip': list of 2D arrays
- 'wind_speed_700': list of 2D arrays (NOT wind_speed_500!)
- 'times': list of timestamps
- 'lat': 1D array
- 'lon': 1D array

To extract wind at 700 hPa instead of 500 hPa, find where you calculate wind speed in your notebook
and change the pressure level index. For example, if you have:

```python
# OLD (500 hPa):
# p_levels = batch.metadata.atmos_levels  # e.g., (50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000)
# idx_500 = list(p_levels).index(500)
# u_500 = preds_org.atmos_vars['u'][0, -1, idx_500].cpu().numpy()
# v_500 = preds_org.atmos_vars['v'][0, -1, idx_500].cpu().numpy()
# wind_speed = np.sqrt(u_500**2 + v_500**2)

# NEW (700 hPa):
p_levels = batch.metadata.atmos_levels
idx_700 = list(p_levels).index(700)
u_700 = preds_org.atmos_vars['u'][0, -1, idx_700].cpu().numpy()
v_700 = preds_org.atmos_vars['v'][0, -1, idx_700].cpu().numpy()
wind_speed = np.sqrt(u_700**2 + v_700**2)
```

Then store it with the key 'wind_speed_700':
```python
control_results['wind_speed_700'].append(wind_speed)
```
"""

# This file is just documentation - copy the code above into your notebook
print(__doc__)
