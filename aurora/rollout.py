"""Copyright (c) Microsoft Corporation. Licensed under the MIT license."""

import dataclasses
from typing import Generator

import torch

from aurora.batch import Batch
from aurora.model.aurora_lite import AuroraLite

__all__ = ["rollout", "rollout_with_latents", "forward_batch"]


def rollout(model: AuroraLite, batch: Batch, steps: int) -> Generator[Batch, None, None]:
    """Perform a roll-out to make long-term predictions.

    Args:
        model (:class:`aurora.model.aurora_lite.AuroraLite`): The model to roll out.
        batch (:class:`aurora.batch.Batch`): The batch to start the roll-out from.
        steps (int): The number of roll-out steps.

    Yields:
        :class:`aurora.batch.Batch`: The prediction after every step.
    """
    # We will need to concatenate data, so ensure that everything is already of the right form.
    # Use an arbitary parameter of the model to derive the data type and device.
    p = next(model.parameters())
    batch = batch.type(p.dtype)
    batch = batch.crop(model.patch_size)
    batch = batch.to(p.device)

    for _ in range(steps):
        pred, _ = model.forward(batch)  # AuroraLite returns (pred, latent_decoder)

        yield pred

        # Add the appropriate history so the model can be run on the prediction.
        batch = dataclasses.replace(
            pred,
            surf_vars={
                k: torch.cat([batch.surf_vars[k][:, 1:], v], dim=1)
                for k, v in pred.surf_vars.items()
            },
            atmos_vars={
                k: torch.cat([batch.atmos_vars[k][:, 1:], v], dim=1)
                for k, v in pred.atmos_vars.items()
            },
        )


def rollout_with_latents(
    model: AuroraLite, batch: Batch, steps: int
) -> Generator[tuple[Batch, torch.Tensor], None, None]:
    """Perform a roll-out to make long-term predictions, yielding both predictions and latents.

    This is a memory-efficient alternative to `forward_batch` that yields results one step at a time,
    allowing for immediate processing and memory cleanup. This is particularly useful when working
    with decoder models that need the latent representations.

    Args:
        model (:class:`aurora.model.aurora_lite.AuroraLite`): The model to roll out.
        batch (:class:`aurora.batch.Batch`): The batch to start the roll-out from.
        steps (int): The number of roll-out steps.

    Yields:
        tuple[:class:`aurora.batch.Batch`, :class:`torch.Tensor`]: A tuple of (prediction, latent)
            after every step. The latent tensor can be used with decoder models.

    Example:
        >>> for pred_batch, latent in rollout_with_latents(model, initial_batch, steps=4):
        >>>     # Process prediction and latent immediately
        >>>     decoder_output = decoder(latent, pred_batch.metadata.lat, pred_batch.metadata.lon)
        >>>     # Store only what you need (e.g., decoded precipitation)
        >>>     results.append(decoder_output['tp_mswep'].cpu().numpy())
        >>>     # Memory is freed after each iteration
    """
    # We will need to concatenate data, so ensure that everything is already of the right form.
    # Use an arbitary parameter of the model to derive the data type and device.
    p = next(model.parameters())
    batch = batch.type(p.dtype)
    batch = batch.crop(model.patch_size)
    batch = batch.to(p.device)

    for _ in range(steps):
        pred, latent = model.forward(batch)  # AuroraLite returns (pred, latent_decoder)

        yield pred, latent

        # Add the appropriate history so the model can be run on the prediction.
        batch = dataclasses.replace(
            pred,
            surf_vars={
                k: torch.cat([batch.surf_vars[k][:, 1:], v], dim=1)
                for k, v in pred.surf_vars.items()
            },
            atmos_vars={
                k: torch.cat([batch.atmos_vars[k][:, 1:], v], dim=1)
                for k, v in pred.atmos_vars.items()
            },
        )


def forward_batch(model: AuroraLite, batch: Batch, steps: int) -> tuple[list[Batch], list[torch.Tensor]]:
    """Run multiple Aurora forward passes while keeping the internal roll-out state.

    Args:
        model: AuroraLite model to evaluate.
        batch: Initial conditions passed to the model.
        steps: Number of sequential 6-hour steps to evaluate.

    Returns:
        Tuple containing per-step Batch predictions and latent decoder tensors.
    """
    if steps < 1:
        raise ValueError('steps must be >= 1')

    p = next(model.parameters())
    batch = batch.type(p.dtype)
    batch = batch.crop(model.patch_size)
    batch = batch.to(p.device)

    preds: list[Batch] = []
    latents: list[torch.Tensor] = []

    for _ in range(steps):
        pred, latent = model.forward(batch)
        preds.append(pred)
        latents.append(latent)

        batch = dataclasses.replace(
            pred,
            surf_vars={
                k: torch.cat([batch.surf_vars[k][:, 1:], v], dim=1)
                for k, v in pred.surf_vars.items()
            },
            atmos_vars={
                k: torch.cat([batch.atmos_vars[k][:, 1:], v], dim=1)
                for k, v in pred.atmos_vars.items()
            },
        )

    return preds, latents
