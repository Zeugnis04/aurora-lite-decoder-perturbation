#!/usr/bin/env python3
"""
Multi-step precipitation forecast using forward batch approach (not rollout iterator).
This avoids the redundant forward pass in the rollout approach.
"""

import numpy as np
import xarray as xr
import torch
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import sys

# Add project to path
sys.path.insert(0, '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation')

from aurora.batch import Batch, Metadata
from aurora.model.aurora_lite import AuroraLite
from aurora.model.decoder_lite import MLPDecoderLite
from transform_data import transform_data
from scipy.ndimage import zoom

# Configuration
test_date_str = "2012-10-24"
ERA5_DATA_PATH = Path("/content/drive/MyDrive/Research")
MSWEP_DATA_PATH = "./MSWEP_V280"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"Testing forward batch approach for {test_date_str}")
print("=" * 70)

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
print(f"\nLoading ERA5 for {test_date_str}...")
date = pd.to_datetime(test_date_str)

static_vars_ds = xr.open_dataset(ERA5_DATA_PATH / "static.nc", engine="h5netcdf")
static_vars_ds = static_vars_ds.sel(latitude=static_vars_ds.latitude[:720])

surf_vars_ds = xr.open_dataset(ERA5_DATA_PATH / f"{test_date_str}-surface-level.nc", engine="h5netcdf")
surf_vars_ds = surf_vars_ds.sel(latitude=surf_vars_ds.latitude[:720])

atmos_vars_ds = xr.open_dataset(ERA5_DATA_PATH / f"{test_date_str}-atmospheric.nc", engine="h5netcdf")
atmos_vars_ds = atmos_vars_ds.sel(latitude=atmos_vars_ds.latitude[:720])

# Create initial batch
initial_batch = Batch(
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

# Multi-step forecast using forward batch approach
print("\nRunning 4-step forecast using forward batch approach...")
print("(Single forward pass per step, no rollout iterator)")

num_steps = 4
precip_predictions = []
current_batch = initial_batch

with torch.inference_mode():
    for i in range(num_steps):
        print(f"  Step {i+1}/{num_steps}: +{(i+1)*6}h forecast...")

        # Single forward pass - gets both predictions and latent
        preds_org, lat_dec = modelAurora.forward(current_batch)

        # Apply decoder to latent
        latent_decoder = lat_dec.detach().clone()
        preds_decoder = modelDecoder.forward(
            latent_decoder,
            current_batch.metadata.lat,
            current_batch.metadata.lon
        )

        # Transform precipitation back to original scale (meters)
        precip = transform_data(
            preds_decoder['tp_mswep'].cpu().numpy().squeeze(),
            'tp_mswep',
            direct=False
        )
        precip_predictions.append(precip)

        print(f"    Precipitation: mean={precip.mean()*1000:.3f} mm, max={precip.max()*1000:.3f} mm")

        # Build next batch from predictions
        current_batch.surf_vars = {
            key: preds_org.surf_vars[key]
            for key in current_batch.surf_vars.keys()
        }

        current_batch.atmos_vars = {
            key: preds_org.atmos_vars[key]
            for key in current_batch.atmos_vars.keys()
        }

        # Update metadata time
        prev_time = current_batch.metadata.time[0]
        if isinstance(prev_time, str):
            prev_time = datetime.fromisoformat(prev_time.replace('Z', '+00:00'))
        new_time = prev_time + timedelta(hours=6)
        current_batch.metadata = Metadata(
            lat=current_batch.metadata.lat,
            lon=current_batch.metadata.lon,
            time=(new_time,),
            atmos_levels=current_batch.metadata.atmos_levels,
        )

        if (i + 1) % 4 == 0:
            torch.cuda.empty_cache()

print(f"\n✓ Generated {len(precip_predictions)} precipitation forecasts")

# Load MSWEP ground truth
def load_mswep_6hourly(date_str, hour):
    """Load and sum two 3-hourly MSWEP periods"""
    date_obj = pd.to_datetime(date_str)
    day_of_year = date_obj.timetuple().tm_yday
    year = date_obj.year

    # First 3-hour period
    filename1 = f"{year}{day_of_year:03d}.{hour:02d}.nc"
    local_file1 = Path(f"./MSWEP_local/{year}/{filename1}")
    ds1 = xr.open_dataset(local_file1)
    precip1 = ds1['precipitation'].values.squeeze() / 1000.0  # mm to meters

    # Second 3-hour period (3 hours later)
    second_time = date_obj + timedelta(hours=3)
    second_day_of_year = second_time.timetuple().tm_yday
    second_hour = (hour + 3) % 24
    filename2 = f"{year}{second_day_of_year:03d}.{second_hour:02d}.nc"
    local_file2 = Path(f"./MSWEP_local/{year}/{filename2}")
    ds2 = xr.open_dataset(local_file2)
    precip2 = ds2['precipitation'].values.squeeze() / 1000.0  # mm to meters

    # Sum and regrid
    precip_6h = precip1 + precip2
    precip_regridded = zoom(precip_6h, 0.4, order=1)  # 0.1° -> 0.25°

    return precip_regridded

print("\nLoading MSWEP 6-hourly ground truth...")
ground_truth = []
for step in range(num_steps):
    forecast_time = date + timedelta(hours=step*6)
    gt = load_mswep_6hourly(forecast_time.strftime("%Y-%m-%d"), forecast_time.hour)
    ground_truth.append(gt)
    print(f"  +{(step+1)*6}h: mean={gt.mean()*1000:.3f} mm, max={gt.max()*1000:.3f} mm")

# Compute metrics
print("\n" + "=" * 70)
print("EVALUATION METRICS")
print("=" * 70)

for step in range(num_steps):
    pred = precip_predictions[step]
    truth = ground_truth[step]

    mae = np.mean(np.abs(pred - truth)) * 1000
    rmse = np.sqrt(np.mean((pred - truth)**2)) * 1000
    bias = np.mean(pred - truth) * 1000

    print(f"\n+{(step+1)*6}h forecast:")
    print(f"  MAE:  {mae:.3f} mm/6h")
    print(f"  RMSE: {rmse:.3f} mm/6h")
    print(f"  Bias: {bias:.3f} mm/6h")

print("\n✓ Forward batch forecast completed!")
