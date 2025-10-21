"""
Quick script to check initial precipitation conditions (t=0)
Compare MSWEP ground truth vs Aurora decoder output at initial time
"""

import numpy as np
import xarray as xr
import torch
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add project to path
import sys
sys.path.insert(0, '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation')

from aurora.batch import Batch, Metadata
from aurora.model.aurora_lite import AuroraLite
from aurora.model.decoder_lite import MLPDecoderLite
from transform_data import transform_data

# Configuration
test_date_str = "2012-10-24"
test_hour = 0
ERA5_DATA_PATH = Path("/content/drive/MyDrive/Research")
MSWEP_DATA_PATH = "./MSWEP_V280"

print(f"Checking initial conditions for {test_date_str} at {test_hour:02d}:00 UTC")
print("="*70)

# Load MSWEP at t=0
from scipy.ndimage import zoom

def load_mswep_t0(date_str, hour):
    """Load MSWEP and regrid to Aurora resolution"""
    date = pd.to_datetime(date_str)
    day_of_year = date.timetuple().tm_yday
    year = date.year
    filename = f"{year}{day_of_year:03d}.{hour:02d}.nc"

    # Try local first
    local_file = Path(f"./MSWEP_local/{year}/{filename}")
    if local_file.exists():
        data_file = local_file
    else:
        data_file = Path(f"{MSWEP_DATA_PATH}/Past/3hourly/{filename}")

    print(f"\nLoading MSWEP from: {data_file}")
    ds = xr.open_dataset(data_file)
    precip_data = ds['precipitation'].values.squeeze()

    print(f"MSWEP native shape: {precip_data.shape}")
    print(f"MSWEP native range: [{precip_data.min():.6f}, {precip_data.max():.6f}] meters")
    print(f"MSWEP native mean: {precip_data.mean():.6f} meters")

    # Regrid to 720x1440
    zoom_factor = 0.4  # 0.1° -> 0.25°
    precip_regridded = zoom(precip_data, zoom_factor, order=1)

    print(f"MSWEP regridded shape: {precip_regridded.shape}")
    print(f"MSWEP regridded range: [{precip_regridded.min():.6f}, {precip_regridded.max():.6f}] meters")
    print(f"MSWEP regridded mean: {precip_regridded.mean():.6f} meters")

    return precip_regridded

# Load Aurora decoder output at t=0
def get_aurora_decoder_t0(date_str):
    """Get decoder output from initial ERA5 conditions"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load models
    print("\nLoading Aurora model...")
    modelAurora = AuroraLite(
        use_lora=False,
        autocast=True,
        surf_vars=("2t", "10u", "10v", "msl"),
        static_vars=("lsm", "z", "slt"),
        atmos_vars=("z", "u", "v", "t", "q")
    )
    modelAurora.load_checkpoint("microsoft/aurora", "aurora-0.25-pretrained.ckpt", strict=False)
    modelAurora = modelAurora.to(device).eval()

    print("Loading decoder model...")
    surf_vars_new = ["tp_mswep", "pe", "r", "swc"]
    modelDecoder = MLPDecoderLite(
        surf_vars_new=surf_vars_new,
        patch_size=modelAurora.decoder.patch_size,
        embed_dim=2*modelAurora.encoder.embed_dim,
        hidden_dims=[512, 512, 256],
    )
    checkpoint = torch.load("./lite-decoder.ckpt", map_location=device)
    modelDecoder.load_state_dict(checkpoint)
    modelDecoder = modelDecoder.to(device).eval()

    # Load ERA5 data
    print(f"\nLoading ERA5 for {date_str}...")
    date = pd.to_datetime(date_str)

    static_vars_ds = xr.open_dataset(ERA5_DATA_PATH / "static.nc", engine="h5netcdf")
    static_vars_ds = static_vars_ds.sel(latitude=static_vars_ds.latitude[:720])

    surf_vars_ds = xr.open_dataset(ERA5_DATA_PATH / f"{date_str}-surface-level.nc", engine="h5netcdf")
    surf_vars_ds = surf_vars_ds.sel(latitude=surf_vars_ds.latitude[:720])

    atmos_vars_ds = xr.open_dataset(ERA5_DATA_PATH / f"{date_str}-atmospheric.nc", engine="h5netcdf")
    atmos_vars_ds = atmos_vars_ds.sel(latitude=atmos_vars_ds.latitude[:720])

    # Create batch
    batch = Batch(
        surf_vars={
            "2t": torch.from_numpy(surf_vars_ds["t2m"].values[:2][None]),
            "10u": torch.from_numpy(surf_vars_ds["u10"].values[:2][None]),
            "10v": torch.from_numpy(surf_vars_ds["v10"].values[:2][None]),
            "msl": torch.from_numpy(surf_vars_ds["msl"].values[:2][None]),
        },
        static_vars={
            "z": torch.from_numpy(static_vars_ds["z"].values[0]),
            "slt": torch.from_numpy(static_vars_ds["slt"].values[0]),
            "lsm": torch.from_numpy(static_vars_ds["lsm"].values[0]),
        },
        atmos_vars={
            "t": torch.from_numpy(atmos_vars_ds["t"].values[:2][None]),
            "u": torch.from_numpy(atmos_vars_ds["u"].values[:2][None]),
            "v": torch.from_numpy(atmos_vars_ds["v"].values[:2][None]),
            "q": torch.from_numpy(atmos_vars_ds["q"].values[:2][None]),
            "z": torch.from_numpy(atmos_vars_ds["z"].values[:2][None]),
        },
        metadata=Metadata(
            lat=torch.from_numpy(surf_vars_ds.latitude.values),
            lon=torch.from_numpy(surf_vars_ds.longitude.values),
            time=(surf_vars_ds.valid_time.values.astype("datetime64[s]").tolist()[1],),
            atmos_levels=tuple(int(level) for level in atmos_vars_ds.pressure_level.values),
        ),
    )

    # Run through Aurora + decoder
    print("\nRunning Aurora + decoder on initial conditions...")
    with torch.inference_mode():
        _, lat_dec = modelAurora.forward(batch)
        decoder_preds = modelDecoder.forward(
            lat_dec.detach().clone(),
            batch.metadata.lat,
            batch.metadata.lon
        )

    # Transform back
    precip_aurora = transform_data(
        decoder_preds['tp_mswep'].cpu().numpy().squeeze(),
        'tp_mswep',
        direct=False
    )

    print(f"Aurora decoder output shape: {precip_aurora.shape}")
    print(f"Aurora decoder output range: [{precip_aurora.min():.6f}, {precip_aurora.max():.6f}] meters")
    print(f"Aurora decoder output mean: {precip_aurora.mean():.6f} meters")

    return precip_aurora

# Load both
mswep_t0 = load_mswep_t0(test_date_str, test_hour)
aurora_t0 = get_aurora_decoder_t0(test_date_str)

# Compare
print("\n" + "="*70)
print("COMPARISON SUMMARY")
print("="*70)
print(f"MSWEP t=0:  shape={mswep_t0.shape}, mean={mswep_t0.mean()*1000:.3f} mm, max={mswep_t0.max()*1000:.3f} mm")
print(f"Aurora t=0: shape={aurora_t0.shape}, mean={aurora_t0.mean()*1000:.3f} mm, max={aurora_t0.max()*1000:.3f} mm")
print(f"Difference: mean={((aurora_t0-mswep_t0)*1000).mean():.3f} mm")

# Visualize
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# MSWEP
im0 = axes[0].imshow(mswep_t0 * 1000, cmap='Blues', vmin=0, vmax=max(mswep_t0.max()*1000, 1))
axes[0].set_title(f'MSWEP t=0\n{test_date_str} {test_hour:02d}:00 UTC')
plt.colorbar(im0, ax=axes[0], label='mm/3h')

# Aurora decoder
im1 = axes[1].imshow(aurora_t0 * 1000, cmap='Blues', vmin=0, vmax=max(aurora_t0.max()*1000, 1))
axes[1].set_title(f'Aurora Decoder t=0\n{test_date_str} {test_hour:02d}:00 UTC')
plt.colorbar(im1, ax=axes[1], label='mm/3h')

# Difference
diff = (aurora_t0 - mswep_t0) * 1000
vmax_diff = max(abs(diff.min()), abs(diff.max()), 0.1)
im2 = axes[2].imshow(diff, cmap='RdBu_r', vmin=-vmax_diff, vmax=vmax_diff)
axes[2].set_title(f'Difference (Aurora - MSWEP)')
plt.colorbar(im2, ax=axes[2], label='mm/3h')

plt.tight_layout()
plt.savefig('initial_condition_comparison.png', dpi=150, bbox_inches='tight')
print(f"\nSaved comparison plot to: initial_condition_comparison.png")
plt.show()
