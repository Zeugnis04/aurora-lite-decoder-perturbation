# Rollout Methods Comparison

This document compares the three different approaches for multi-step forecasting with Aurora.

## Overview of Methods

| Method | Returns Latents? | Memory Usage | Use Case |
|--------|-----------------|--------------|----------|
| `rollout` | ❌ No | Low (1×) | Standard Aurora rollout without decoder |
| `forward_batch` | ✅ Yes | High (N×) | Need all results at once, small N |
| `rollout_with_latents` | ✅ Yes | Low (1×) | **Memory-efficient decoder inference** |

## Method 1: `rollout` (Standard)

```python
from aurora.rollout import rollout

# Generator that yields predictions only
for pred in rollout(model, batch, steps=4):
    # pred is a Batch object
    # NO latent available for decoder
    print(pred.surf_vars['tp'])  # Can access Aurora's precipitation
```

**Pros:**
- Memory efficient
- Simple to use

**Cons:**
- ❌ **Cannot use with decoder models** (no latent)
- Limited to Aurora's native output variables

## Method 2: `forward_batch` (Old Decoder Approach)

```python
from aurora.rollout import forward_batch

# Returns ALL results at once
preds, latents = forward_batch(model, batch, steps=4)

# Process all 4 steps
for i in range(4):
    pred_batch = preds[i]
    latent = latents[i]
    decoder_out = decoder(latent, ...)
    results.append(decoder_out)
```

**Memory Timeline:**
```
Step 1: Store pred[0] + latent[0]  →  Memory: 1×
Step 2: Store pred[1] + latent[1]  →  Memory: 2×
Step 3: Store pred[2] + latent[2]  →  Memory: 3×
Step 4: Store pred[3] + latent[3]  →  Memory: 4×
Process all                         →  Memory: 4×  ⚠️ PEAK USAGE
```

**Pros:**
- ✅ Provides latents for decoder
- All results available simultaneously

**Cons:**
- ❌ **High memory usage** (accumulates N steps)
- ❌ **Causes CUDA OOM** with large models or many steps
- Must wait for all steps to complete before processing

**When to use:**
- Very short rollouts (1-2 steps)
- Need to process all steps together
- Have abundant GPU memory

## Method 3: `rollout_with_latents` (New, Recommended)

```python
from aurora.rollout import rollout_with_latents

results = []

# Generator yields one step at a time
for pred_batch, latent in rollout_with_latents(model, batch, steps=4):
    # Process immediately
    decoder_out = decoder(latent.detach(), ...)
    results.append(decoder_out.cpu().numpy())

    # Clean up before next iteration
    del decoder_out, latent
    torch.cuda.empty_cache()
```

**Memory Timeline:**
```
Step 1: pred[0] + latent[0]  →  process  →  delete  →  Memory: 1×
Step 2: pred[1] + latent[1]  →  process  →  delete  →  Memory: 1×
Step 3: pred[2] + latent[2]  →  process  →  delete  →  Memory: 1×
Step 4: pred[3] + latent[3]  →  process  →  delete  →  Memory: 1×
                                                         ✅ CONSTANT
```

**Pros:**
- ✅ **Memory efficient** (constant usage)
- ✅ **Works with decoder models** (provides latents)
- ✅ **No CUDA OOM errors**
- Immediate processing (can see progress)
- Scales to any number of steps

**Cons:**
- Must process each step as it's yielded
- Cannot access all steps simultaneously

**When to use:**
- ✅ **Decoder-based inference** (our use case!)
- Long rollouts (4+ steps)
- Limited GPU memory
- Large models (Aurora-Lite)

## Real Example: MSWEP Precipitation Evaluation

### Problem with `forward_batch`:

```python
# Cell 18 in notebook - FAILS with OOM!
predictions = forecast_with_decoder_forward_batch(modelAurora, modelDecoder, initial_batch, 4)
```

```
OutOfMemoryError: CUDA out of memory.
Tried to allocate 254.00 MiB. GPU 0 has a total capacity of 79.32 GiB
of which 209.88 MiB is free. Process has 79.10 GiB memory in use.
```

### Solution with `rollout_with_latents`:

```python
def forecast_with_decoder_forward_batch(modelAurora, modelDecoder, initial_batch, steps):
    """Memory-efficient forecasting using generator approach."""
    precip_predictions = []

    with torch.inference_mode():
        # Process one step at a time - no accumulation!
        for pred_batch, latent in rollout_with_latents(modelAurora, initial_batch, steps):
            # Decode latent to precipitation
            decoder_out = modelDecoder(
                latent.detach(),
                pred_batch.metadata.lat,
                pred_batch.metadata.lon,
            )

            # Transform and store only final result (meters)
            precip = transform_data(
                decoder_out["tp_mswep"].cpu().numpy().squeeze(),
                "tp_mswep",
                direct=False,
            )
            precip_predictions.append(precip)

            # Free memory immediately
            del decoder_out, latent
            torch.cuda.empty_cache()

    return precip_predictions
```

**Result:** ✅ Runs successfully without OOM errors!

## Memory Usage Comparison

For Aurora-Lite with 4-step rollout:

| Component | Size (approx) | forward_batch | rollout_with_latents |
|-----------|--------------|---------------|---------------------|
| Batch (surf) | ~2 GB | 4× = 8 GB | 1× = 2 GB |
| Batch (atmos) | ~10 GB | 4× = 40 GB | 1× = 10 GB |
| Latent | ~5 GB | 4× = 20 GB | 1× = 5 GB |
| **TOTAL** | - | **~68 GB** ⚠️ | **~17 GB** ✅ |

*Numbers are approximate and vary by batch size and resolution*

## Migration Guide

If you're currently using `forward_batch` with a decoder:

### Before:
```python
from aurora.rollout import forward_batch

preds, latents = forward_batch(model, batch, steps)
results = [decoder(lat, ...) for lat in latents]
```

### After:
```python
from aurora.rollout import rollout_with_latents

results = []
for pred, latent in rollout_with_latents(model, batch, steps):
    result = decoder(latent.detach(), ...)
    results.append(result.cpu().numpy())
    del latent
    torch.cuda.empty_cache()
```

## Conclusion

For decoder-based multi-step forecasting (especially with MSWEP precipitation evaluation):

✅ **Use `rollout_with_latents`** - it's the memory-efficient solution that provides both predictions and latents without accumulating intermediate results.

The generator pattern is the key: it allows data to flow efficiently through the rollout → decoder → results pipeline while maintaining constant memory usage.
