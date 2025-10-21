#!/usr/bin/env python3
"""
Create a diagram illustrating the multiperturbation approach for weather prediction.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import numpy as np

# Set up the figure
fig, ax = plt.subplots(1, 1, figsize=(16, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Define colors
color_initial = '#E8F4F8'
color_perturbation = '#FFE5E5'
color_forecast = '#E8F5E9'
color_analysis = '#FFF9E6'
color_700hpa = '#D1C4E9'

# Title
ax.text(5, 9.5, 'Multi-Perturbation Ensemble Weather Prediction Framework',
        fontsize=18, fontweight='bold', ha='center', va='top')
ax.text(5, 9.1, 'Using Aurora-Lite with 700 hPa Wind Analysis',
        fontsize=12, style='italic', ha='center', va='top', color='#666')

# ========== SECTION 1: Initial Conditions ==========
y_start = 8.2
box_height = 0.6
box_width = 1.8

# Initial conditions box
initial_box = FancyBboxPatch((0.5, y_start - box_height), box_width, box_height,
                             boxstyle="round,pad=0.05",
                             edgecolor='#2196F3', facecolor=color_initial, linewidth=2)
ax.add_patch(initial_box)
ax.text(0.5 + box_width/2, y_start - box_height/2, 'Initial Conditions\n(t₀ = 2012-10-24)',
        fontsize=10, ha='center', va='center', fontweight='bold')

# Atmospheric variables
var_y = y_start - 1.3
ax.text(0.5 + box_width/2, var_y, 'Atmospheric State:', fontsize=9, ha='center', fontweight='bold')
variables = [
    'T (temperature)',
    'u, v (winds)',
    'q (humidity)',
    'z (geopotential)',
    'Surface: 2t, 10u, 10v, msl'
]
for i, var in enumerate(variables):
    ax.text(0.5 + box_width/2, var_y - 0.25 - i*0.15, f'• {var}', fontsize=7, ha='center')

# ========== SECTION 2: Perturbation Strategy ==========
pert_x_start = 3.0
pert_y_start = y_start

# Perturbation box
ax.text(pert_x_start + 1.5, pert_y_start + 0.3, 'Perturbation Strategy',
        fontsize=11, ha='center', fontweight='bold', color='#D32F2F')

# Multiple perturbation scenarios
perturbations = [
    {'name': 'Control', 'offset': 0, 'color': '#90CAF9'},
    {'name': 'Pacific\nPerturbation', 'offset': 1.2, 'color': '#FFAB91'},
    {'name': 'Atlantic\nPerturbation', 'offset': 2.4, 'color': '#FFCC80'},
    {'name': 'Arctic\nPerturbation', 'offset': 3.6, 'color': '#CE93D8'},
]

for i, pert in enumerate(perturbations):
    pert_box = FancyBboxPatch((pert_x_start, pert_y_start - pert['offset'] - 0.5), 1.5, 0.4,
                              boxstyle="round,pad=0.03",
                              edgecolor='#D32F2F' if i > 0 else '#666',
                              facecolor=pert['color'],
                              linewidth=2 if i > 0 else 1,
                              linestyle='-' if i > 0 else '--')
    ax.add_patch(pert_box)
    ax.text(pert_x_start + 0.75, pert_y_start - pert['offset'] - 0.3, pert['name'],
            fontsize=8, ha='center', va='center', fontweight='bold' if i > 0 else 'normal')

    # Add perturbation details for non-control
    if i > 0:
        ax.text(pert_x_start + 1.6, pert_y_start - pert['offset'] - 0.3,
                f'ΔT ~ {np.random.randint(1, 4)} K\n700-925 hPa',
                fontsize=6, ha='left', va='center', style='italic')

# Arrow from initial to perturbations
arrow1 = FancyArrowPatch((0.5 + box_width, y_start - box_height/2),
                         (pert_x_start, y_start - 0.3),
                         arrowstyle='->', mutation_scale=20, linewidth=2, color='#666')
ax.add_artist(arrow1)

# ========== SECTION 3: Forecast Model ==========
model_x = 5.2
model_y = y_start - 1.5

# Model box
model_box = FancyBboxPatch((model_x, model_y - 0.8), 2.0, 1.6,
                           boxstyle="round,pad=0.1",
                           edgecolor='#388E3C', facecolor=color_forecast, linewidth=3)
ax.add_patch(model_box)

ax.text(model_x + 1.0, model_y + 0.5, 'Aurora-Lite Forecast',
        fontsize=11, ha='center', fontweight='bold', color='#388E3C')
ax.text(model_x + 1.0, model_y + 0.15, 'with Decoders',
        fontsize=9, ha='center', style='italic')

# Model components
ax.text(model_x + 0.2, model_y - 0.1, '• Encoder (atmospheric)', fontsize=7, ha='left')
ax.text(model_x + 0.2, model_y - 0.3, '• 3D Swin Transformer', fontsize=7, ha='left')
ax.text(model_x + 0.2, model_y - 0.5, '• MLP Decoder (hydrology)', fontsize=7, ha='left')

# Timesteps
ax.text(model_x + 1.0, model_y - 0.9, 'Δt = 6 hours × 28 steps',
        fontsize=7, ha='center', style='italic', color='#666')

# Arrows from perturbations to model
for i, pert in enumerate(perturbations):
    arrow = FancyArrowPatch((pert_x_start + 1.5, pert_y_start - pert['offset'] - 0.3),
                           (model_x, model_y),
                           arrowstyle='->', mutation_scale=15, linewidth=1.5,
                           color=pert['color'], alpha=0.7)
    ax.add_artist(arrow)

# ========== SECTION 4: Output Variables ==========
output_x = 7.8
output_y_start = y_start

# Output box
ax.text(output_x + 0.9, output_y_start + 0.3, 'Forecast Outputs',
        fontsize=11, ha='center', fontweight='bold', color='#F57C00')

outputs = [
    {'name': 'Precipitation\n(6-hr accumulation)', 'color': '#BBDEFB', 'icon': '🌧️'},
    {'name': '700 hPa Wind Speed\n(from u, v components)', 'color': color_700hpa, 'icon': '💨'},
]

for i, output in enumerate(outputs):
    out_y = output_y_start - i*1.2 - 0.5
    output_box = FancyBboxPatch((output_x, out_y), 1.8, 0.7,
                                boxstyle="round,pad=0.05",
                                edgecolor='#F57C00', facecolor=output['color'], linewidth=2)
    ax.add_patch(output_box)
    ax.text(output_x + 0.1, out_y + 0.35, output['icon'], fontsize=16, ha='left', va='center')
    ax.text(output_x + 0.9, out_y + 0.35, output['name'],
            fontsize=8, ha='center', va='center', fontweight='bold')

# Arrow from model to outputs
arrow_out = FancyArrowPatch((model_x + 2.0, model_y),
                           (output_x, output_y_start - 0.3),
                           arrowstyle='->', mutation_scale=20, linewidth=2, color='#666')
ax.add_artist(arrow_out)

# ========== SECTION 5: Analysis Methods ==========
analysis_y = 2.5

# Analysis box
analysis_box = FancyBboxPatch((0.5, analysis_y - 1.5), 9.0, 1.8,
                              boxstyle="round,pad=0.1",
                              edgecolor='#F9A825', facecolor=color_analysis, linewidth=2,
                              linestyle='--')
ax.add_patch(analysis_box)

ax.text(5.0, analysis_y + 0.2, 'Ensemble Analysis & Visualization',
        fontsize=12, ha='center', fontweight='bold', color='#F9A825')

# Analysis methods in columns
analysis_methods = [
    {
        'title': 'Difference Analysis',
        'items': ['Perturbed - Control', 'Spatial patterns', 'Temporal evolution'],
        'x': 1.5
    },
    {
        'title': 'Statistical Metrics',
        'items': ['Mean/Std deviation', 'Max differences', 'Regional impacts'],
        'x': 4.0
    },
    {
        'title': 'Visualization',
        'items': ['Individual timesteps', 'Side-by-side comparison', 'Difference maps'],
        'x': 6.5
    },
    {
        'title': 'Key Innovation',
        'items': ['700 hPa analysis', 'Mid-troposphere focus', 'Better for synoptic'],
        'x': 8.8
    }
]

for method in analysis_methods:
    ax.text(method['x'], analysis_y - 0.2, method['title'],
            fontsize=8, ha='center', fontweight='bold', color='#E65100')
    for i, item in enumerate(method['items']):
        ax.text(method['x'], analysis_y - 0.5 - i*0.25, f'• {item}',
                fontsize=6.5, ha='center')

# ========== SECTION 6: Scientific Goals ==========
goals_y = 0.5

ax.text(5.0, goals_y, 'Scientific Goals: Quantify butterfly effect, assess predictability limits, ' +
                      'improve ensemble forecasting at 700 hPa (jet stream level)',
        fontsize=8, ha='center', style='italic', color='#424242',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#EEEEEE', alpha=0.8))

# ========== Add 700 hPa Highlight Box ==========
hpa_box = FancyBboxPatch((8.5, 5.5), 1.3, 1.2,
                         boxstyle="round,pad=0.08",
                         edgecolor='#7E57C2', facecolor=color_700hpa, linewidth=3,
                         linestyle='-')
ax.add_patch(hpa_box)

ax.text(9.15, 6.4, '700 hPa Level', fontsize=10, ha='center', fontweight='bold', color='#4A148C')
ax.text(9.15, 6.1, 'Why Important?', fontsize=8, ha='center', fontweight='bold', color='#4A148C')
importance_text = [
    '• Jet stream dynamics',
    '• Weather systems',
    '• Better than 500 hPa',
    '• Mid-troposphere'
]
for i, text in enumerate(importance_text):
    ax.text(9.15, 5.85 - i*0.18, text, fontsize=6, ha='center')

# Save the figure
output_path = '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/multiperturbation_diagram.png'
plt.tight_layout()
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✓ Diagram saved to: {output_path}")

# Also save as PDF for publications
pdf_path = output_path.replace('.png', '.pdf')
plt.savefig(pdf_path, bbox_inches='tight', facecolor='white')
print(f"✓ PDF version saved to: {pdf_path}")

plt.show()
print("\n" + "="*70)
print("Diagram successfully created!")
print("="*70)
