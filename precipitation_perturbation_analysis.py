#!/usr/bin/env python3
"""
Precipitation Perturbation Analysis using Aurora-Lite with Decoders
Based on methodology from PerturbationTries.ipynb

This script:
1. Runs aurora-lite-decoder for baseline (no perturbation)
2. Runs aurora-lite-decoder with temperature perturbation
3. Compares precipitation changes between scenarios
"""

import sys
import os
import numpy as np
import h5py
import xarray as xr
import torch
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from pathlib import Path

# Add the project directory to Python path
project_dir = os.path.abspath('.')
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from aurora.batch import Batch, Metadata
from aurora.model.aurora_lite import AuroraLite
from aurora.model.decoder_lite import MLPDecoderLite
from transform_data import transform_data

class PrecipitationPerturbationAnalysis:
    def __init__(self, data_path="./data/downloads"):
        self.data_path = Path(data_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Perturbation parameters (from PerturbationTries.ipynb)
        self.Lv = 2.5e6       # Latent heat of vaporization [J/kg]
        self.cp = 1005        # Specific heat at constant pressure [J/kg·K]
        self.delta_q = 0.0010 # Specific humidity perturbation
        self.delta_T = (self.Lv * self.delta_q) / self.cp  # Temperature perturbation
        self.sigma = 8.0      # Gaussian spread parameter

        # Default perturbation center (can be modified)
        self.center_lat = 60.0
        self.center_lon = -147.0

        # Pressure levels for perturbation (700-925 hPa)
        self.perturb_levels = [700, 850, 925]

        print(f"Using device: {self.device}")
        print(f"Temperature perturbation amplitude: {self.delta_T:.3f} K")

    def load_models(self):
        """Load Aurora-Lite and decoder models"""
        print("Loading Aurora-Lite model...")

        # Initialize Aurora model
        self.modelAurora = AuroraLite(
            use_lora=False,
            autocast=True,
            surf_vars=("2t", "10u", "10v", "msl"),
            static_vars=("lsm", "z", "slt"),
            atmos_vars=("z", "u", "v", "t", "q")
        )

        self.modelAurora.load_checkpoint("microsoft/aurora", "aurora-0.25-pretrained.ckpt")
        self.modelAurora = self.modelAurora.to(self.device)
        self.modelAurora.eval()

        print("Loading decoder model...")

        # Initialize decoder
        surf_vars_new = ["tp_mswep", "pe", "r", "swc"]
        self.modelDecoder = MLPDecoderLite(
            surf_vars_new=surf_vars_new,
            patch_size=self.modelAurora.decoder.patch_size,
            embed_dim=2*self.modelAurora.encoder.embed_dim,
            hidden_dims=[512, 512, 256],
        )

        checkpoint = torch.load("./lite-decoder.ckpt")
        self.modelDecoder.load_state_dict(checkpoint)
        self.modelDecoder.to(self.device)
        self.modelDecoder.eval()

        print("Models loaded successfully!")

    def load_data(self):
        """Load ERA5 data for 2012-10-24"""
        print("Loading ERA5 data...")

        # Load static variables
        static_vars_ds = xr.open_dataset(self.data_path / "static.nc", engine="netcdf4")
        static_vars_ds = static_vars_ds.sel(latitude=static_vars_ds.latitude[:720])

        # Load surface variables
        surf_vars_ds = xr.open_dataset(self.data_path / "2012-10-24-surface-level.nc", engine="netcdf4")
        surf_vars_ds = surf_vars_ds.sel(latitude=surf_vars_ds.latitude[:720])

        # Load atmospheric variables
        atmos_vars_ds = xr.open_dataset(self.data_path / "2012-10-24-atmospheric.nc", engine="netcdf4")
        atmos_vars_ds = atmos_vars_ds.sel(latitude=atmos_vars_ds.latitude[:720])

        # Create baseline batch
        self.batch_baseline = Batch(
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

        print("Data loaded successfully!")

    def create_gaussian_mask(self):
        """Create Gaussian perturbation mask"""
        lat = self.batch_baseline.metadata.lat.numpy()
        lon = self.batch_baseline.metadata.lon.numpy()

        # Handle longitude wrapping
        center_lon_adj = self.center_lon
        if self.batch_baseline.metadata.lon.max() > 180:
            center_lon_adj = self.center_lon % 360

        # Create meshgrid
        LON, LAT = np.meshgrid(lon, lat)

        # Calculate distances
        dlon = LON - center_lon_adj
        dlat = LAT - self.center_lat

        # Handle longitude wrapping for distance calculation
        dlon = np.where(dlon > 180, dlon - 360, dlon)
        dlon = np.where(dlon < -180, dlon + 360, dlon)

        # Create Gaussian mask
        gaussian_mask = self.delta_T * np.exp(-(dlon**2 + dlat**2) / (2 * self.sigma**2))

        return torch.from_numpy(gaussian_mask).float()

    def create_perturbed_batch(self):
        """Create batch with temperature perturbation"""
        print(f"Creating perturbation at ({self.center_lat}, {self.center_lon})...")

        # Create Gaussian mask
        gaussian_mask_torch = self.create_gaussian_mask()

        # Clone temperature tensor
        t_pert = self.batch_baseline.atmos_vars["t"].clone()  # shape: [B, T, L, H, W]

        # Get pressure levels and find indices for perturbation levels
        p_levels = torch.tensor(self.batch_baseline.metadata.atmos_levels)
        plev_idx = []
        for level in self.perturb_levels:
            try:
                idx = torch.where(p_levels == level)[0][0]
                plev_idx.append(idx)
            except IndexError:
                print(f"Warning: Pressure level {level} hPa not found")

        # Apply perturbation to selected pressure levels
        for i in plev_idx:
            t_pert[0, :, i] += gaussian_mask_torch  # [B=0, T=all, L=i, H, W]

        # Create perturbed batch
        batch_perturbed = Batch(
            surf_vars=self.batch_baseline.surf_vars,
            static_vars=self.batch_baseline.static_vars,
            atmos_vars={
                "t": t_pert,  # Use perturbed temperature
                "u": self.batch_baseline.atmos_vars["u"],
                "v": self.batch_baseline.atmos_vars["v"],
                "q": self.batch_baseline.atmos_vars["q"],
                "z": self.batch_baseline.atmos_vars["z"],
            },
            metadata=self.batch_baseline.metadata,
        )

        print(f"Applied perturbation to pressure levels: {self.perturb_levels} hPa")
        return batch_perturbed

    def run_prediction(self, batch, scenario_name):
        """Run aurora-lite prediction with decoders"""
        print(f"Running {scenario_name} prediction...")

        with torch.inference_mode():
            # Run Aurora prediction
            preds_org, lat_dec = self.modelAurora.forward(batch)

            # Run decoder prediction
            latent_decoder = lat_dec.detach().clone()
            preds_new = self.modelDecoder.forward(
                latent_decoder,
                batch.metadata.lat,
                batch.metadata.lon
            )

        # Transform decoder predictions back to original scale
        preds_transformed = {
            k: transform_data(v.cpu().numpy().squeeze(), k, direct=False)
            for k, v in preds_new.items()
        }

        print(f"Completed {scenario_name} prediction!")
        return preds_org, preds_transformed

    def analyze_precipitation_changes(self, baseline_precip, perturbed_precip):
        """Analyze precipitation changes"""
        print("Analyzing precipitation changes...")

        # Calculate absolute and relative differences
        precip_diff = perturbed_precip - baseline_precip

        # Calculate statistics
        stats = {
            'max_increase': np.max(precip_diff),
            'max_decrease': np.min(precip_diff),
            'mean_change': np.mean(precip_diff),
            'std_change': np.std(precip_diff),
            'total_baseline': np.sum(baseline_precip),
            'total_perturbed': np.sum(perturbed_precip),
            'relative_change': (np.sum(perturbed_precip) - np.sum(baseline_precip)) / np.sum(baseline_precip) * 100
        }

        print(f"Precipitation Change Statistics:")
        print(f"  Max increase: {stats['max_increase']:.3f} mm/6h")
        print(f"  Max decrease: {stats['max_decrease']:.3f} mm/6h")
        print(f"  Mean change: {stats['mean_change']:.3f} mm/6h")
        print(f"  Std change: {stats['std_change']:.3f} mm/6h")
        print(f"  Total baseline: {stats['total_baseline']:.3f} mm")
        print(f"  Total perturbed: {stats['total_perturbed']:.3f} mm")
        print(f"  Relative change: {stats['relative_change']:.2f}%")

        return precip_diff, stats

    def plot_results(self, baseline_precip, perturbed_precip, precip_diff):
        """Plot precipitation comparison"""
        print("Creating plots...")

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Common parameters for precipitation plots
        precip_vmin, precip_vmax = 1e-3, 100
        diff_vmax = np.max(np.abs(precip_diff))

        # Baseline precipitation
        im1 = axes[0, 0].imshow(
            1e3 * baseline_precip,
            extent=(-180, 180, -90, 90),
            cmap='Blues',
            norm=plt.LogNorm(vmin=precip_vmin, vmax=precip_vmax)
        )
        axes[0, 0].set_title('Baseline Precipitation (mm/6h)')
        plt.colorbar(im1, ax=axes[0, 0])

        # Perturbed precipitation
        im2 = axes[0, 1].imshow(
            1e3 * perturbed_precip,
            extent=(-180, 180, -90, 90),
            cmap='Blues',
            norm=plt.LogNorm(vmin=precip_vmin, vmax=precip_vmax)
        )
        axes[0, 1].set_title('Perturbed Precipitation (mm/6h)')
        plt.colorbar(im2, ax=axes[0, 1])

        # Precipitation difference
        im3 = axes[1, 0].imshow(
            1e3 * precip_diff,
            extent=(-180, 180, -90, 90),
            cmap='RdBu_r',
            vmin=-diff_vmax*1e3, vmax=diff_vmax*1e3
        )
        axes[1, 0].set_title('Precipitation Difference (mm/6h)')
        plt.colorbar(im3, ax=axes[1, 0])

        # Perturbation location
        gaussian_mask = self.create_gaussian_mask().numpy()
        im4 = axes[1, 1].imshow(
            gaussian_mask,
            extent=(-180, 180, -90, 90),
            cmap='Reds'
        )
        axes[1, 1].set_title(f'Temperature Perturbation at ({self.center_lat}, {self.center_lon})')
        axes[1, 1].plot(self.center_lon, self.center_lat, 'ko', markersize=8)
        plt.colorbar(im4, ax=axes[1, 1], label='ΔT (K)')

        plt.tight_layout()

        # Save plot
        output_path = f"precipitation_perturbation_analysis_{self.center_lat}_{self.center_lon}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved plot to {output_path}")
        plt.show()

    def run_full_analysis(self, center_lat=None, center_lon=None):
        """Run complete perturbation analysis"""
        print("Starting Precipitation Perturbation Analysis")
        print("=" * 50)

        # Update perturbation center if provided
        if center_lat is not None:
            self.center_lat = center_lat
        if center_lon is not None:
            self.center_lon = center_lon

        # Load models and data
        self.load_models()
        self.load_data()

        # Create perturbed batch
        batch_perturbed = self.create_perturbed_batch()

        # Run baseline prediction
        preds_baseline_org, preds_baseline_new = self.run_prediction(
            self.batch_baseline, "baseline"
        )

        # Run perturbed prediction
        preds_perturbed_org, preds_perturbed_new = self.run_prediction(
            batch_perturbed, "perturbed"
        )

        # Extract precipitation data
        baseline_precip = preds_baseline_new['tp_mswep']
        perturbed_precip = preds_perturbed_new['tp_mswep']

        # Analyze changes
        precip_diff, stats = self.analyze_precipitation_changes(
            baseline_precip, perturbed_precip
        )

        # Create plots
        self.plot_results(baseline_precip, perturbed_precip, precip_diff)

        print("=" * 50)
        print("Analysis complete!")

        return {
            'baseline_precip': baseline_precip,
            'perturbed_precip': perturbed_precip,
            'precip_diff': precip_diff,
            'stats': stats,
            'preds_baseline_org': preds_baseline_org,
            'preds_perturbed_org': preds_perturbed_org,
            'preds_baseline_new': preds_baseline_new,
            'preds_perturbed_new': preds_perturbed_new
        }


if __name__ == "__main__":
    # Initialize analysis
    analyzer = PrecipitationPerturbationAnalysis()

    # Run analysis with default parameters
    results = analyzer.run_full_analysis()

    print("Analysis completed successfully!")