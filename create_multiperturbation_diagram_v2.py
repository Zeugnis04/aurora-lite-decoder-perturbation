#!/usr/bin/env python3
"""
Create a detailed diagram illustrating the iterative multiperturbation approach for weather prediction.
Shows how perturbations are applied at each step, not just initially.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Wedge
import numpy as np

# Set up the figure
fig, ax = plt.subplots(1, 1, figsize=(18, 12))
ax.set_xlim(0, 18)
ax.set_ylim(0, 12)
ax.axis('off')

# Define colors
color_initial = '#E3F2FD'
color_perturbation = '#FFEBEE'
color_forecast = '#E8F5E9'
color_export = '#FFF3E0'
color_700hpa = '#D1C4E9'
color_iteration = '#F3E5F5'

# Title
ax.text(9, 11.5, 'Iterative Multi-Perturbation Ensemble Weather Prediction',
        fontsize=20, fontweight='bold', ha='center', va='top')
ax.text(9, 11.0, 'Perturbations Applied at Each Forecast Step (700 hPa Wind Analysis)',
        fontsize=13, style='italic', ha='center', va='top', color='#666')

# ========== LEFT SIDE: Control Run ==========
control_x = 1.5
y_start = 9.5

ax.text(control_x, y_start + 0.5, 'CONTROL RUN', fontsize=12, ha='center',
        fontweight='bold', color='#1976D2',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#E3F2FD', edgecolor='#1976D2', linewidth=2))

# Initial conditions
init_box = FancyBboxPatch((control_x - 0.6, y_start - 0.5), 1.2, 0.8,
                          boxstyle="round,pad=0.05",
                          edgecolor='#1565C0', facecolor=color_initial, linewidth=2)
ax.add_patch(init_box)
ax.text(control_x, y_start - 0.1, 'Initial State\nt₀', fontsize=9, ha='center', va='center', fontweight='bold')

# Control forecast steps
control_steps_y = [y_start - 2.0, y_start - 4.0, y_start - 6.0]
control_labels = ['t₁ (6h)', 't₂ (12h)', '...', 't₂₈ (168h)']

for i, (y_pos, label) in enumerate(zip(control_steps_y, control_labels[:3])):
    # Forecast box
    forecast_box = FancyBboxPatch((control_x - 0.5, y_pos - 0.3), 1.0, 0.6,
                                  boxstyle="round,pad=0.04",
                                  edgecolor='#388E3C', facecolor=color_forecast, linewidth=2)
    ax.add_patch(forecast_box)
    ax.text(control_x, y_pos, f'Forecast\n{label}', fontsize=8, ha='center', va='center', fontweight='bold')

    # Arrow from previous step
    if i == 0:
        arrow = FancyArrowPatch((control_x, y_start - 0.5), (control_x, y_pos + 0.3),
                               arrowstyle='->', mutation_scale=15, linewidth=2, color='#1565C0')
    else:
        arrow = FancyArrowPatch((control_x, control_steps_y[i-1] - 0.3), (control_x, y_pos + 0.3),
                               arrowstyle='->', mutation_scale=15, linewidth=2, color='#388E3C')
    ax.add_artist(arrow)

# Add dots for continuation
ax.text(control_x, control_steps_y[-1] - 0.8, '⋮', fontsize=24, ha='center', va='center', color='#666')

# Final step
final_y = control_steps_y[-1] - 1.5
forecast_box_final = FancyBboxPatch((control_x - 0.5, final_y - 0.3), 1.0, 0.6,
                                    boxstyle="round,pad=0.04",
                                    edgecolor='#388E3C', facecolor=color_forecast, linewidth=2)
ax.add_patch(forecast_box_final)
ax.text(control_x, final_y, 'Forecast\nt₂₈', fontsize=8, ha='center', va='center', fontweight='bold')

# ========== CENTER: Detailed Iterative Perturbation Flow ==========
pert_x_start = 5.5
flow_y_start = 9.5

ax.text(pert_x_start + 3.0, flow_y_start + 0.5, 'PERTURBED RUN (Iterative Process)',
        fontsize=12, ha='center', fontweight='bold', color='#C62828',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFEBEE', edgecolor='#C62828', linewidth=2))

# Step 0: Initial State
step_y = flow_y_start
step_width = 1.0
step_height = 0.6
spacing = 1.3

# Initial state (same as control)
init_pert_box = FancyBboxPatch((pert_x_start - 0.5, step_y - 0.4), 1.0, 0.8,
                               boxstyle="round,pad=0.05",
                               edgecolor='#1565C0', facecolor=color_initial, linewidth=2)
ax.add_patch(init_pert_box)
ax.text(pert_x_start, step_y, 'Initial State\nt₀', fontsize=8, ha='center', va='center', fontweight='bold')

# Arrow to first perturbation
arrow0 = FancyArrowPatch((pert_x_start + 0.5, step_y), (pert_x_start + 1.5, step_y),
                        arrowstyle='->', mutation_scale=15, linewidth=2, color='#666')
ax.add_artist(arrow0)

# Iteration steps
iterations = [
    {'step': 1, 'time': 't₁ (6h)', 'y_offset': 0},
    {'step': 2, 'time': 't₂ (12h)', 'y_offset': -spacing * 2},
    {'step': '...', 'time': '...', 'y_offset': -spacing * 4},
    {'step': 28, 'time': 't₂₈ (168h)', 'y_offset': -spacing * 6},
]

for idx, iter_info in enumerate(iterations):
    current_y = step_y + iter_info['y_offset']
    step_num = iter_info['step']
    time_label = iter_info['time']

    if step_num == '...':
        # Just show dots
        ax.text(pert_x_start + 3.0, current_y, '⋮', fontsize=32, ha='center', va='center', color='#666')
        continue

    # Step label on left
    ax.text(pert_x_start + 1.0, current_y + 0.5, f'Step {step_num}:',
            fontsize=9, ha='left', va='center', fontweight='bold', color='#C62828')

    # 1. Apply Perturbation
    pert_box = FancyBboxPatch((pert_x_start + 2.0, current_y - 0.25), 1.2, 0.5,
                              boxstyle="round,pad=0.03",
                              edgecolor='#D32F2F', facecolor=color_perturbation, linewidth=2)
    ax.add_patch(pert_box)
    ax.text(pert_x_start + 2.6, current_y, '① Apply\nΔT', fontsize=7, ha='center', va='center', fontweight='bold')

    # Arrow to forecast
    arrow1 = FancyArrowPatch((pert_x_start + 3.2, current_y), (pert_x_start + 3.8, current_y),
                            arrowstyle='->', mutation_scale=12, linewidth=2, color='#D32F2F')
    ax.add_artist(arrow1)

    # 2. Aurora Forecast
    forecast_box = FancyBboxPatch((pert_x_start + 3.8, current_y - 0.25), 1.4, 0.5,
                                  boxstyle="round,pad=0.03",
                                  edgecolor='#388E3C', facecolor=color_forecast, linewidth=2)
    ax.add_patch(forecast_box)
    ax.text(pert_x_start + 4.5, current_y, '② Forecast\n6h', fontsize=7, ha='center', va='center', fontweight='bold')

    # Arrow to export
    arrow2 = FancyArrowPatch((pert_x_start + 5.2, current_y), (pert_x_start + 5.8, current_y),
                            arrowstyle='->', mutation_scale=12, linewidth=2, color='#388E3C')
    ax.add_artist(arrow2)

    # 3. Export Results
    export_box = FancyBboxPatch((pert_x_start + 5.8, current_y - 0.25), 1.2, 0.5,
                                boxstyle="round,pad=0.03",
                                edgecolor='#F57C00', facecolor=color_export, linewidth=2)
    ax.add_patch(export_box)
    ax.text(pert_x_start + 6.4, current_y, f'③ Export\n{time_label}', fontsize=7, ha='center', va='center', fontweight='bold')

    # Loop back arrow to next perturbation (except for last step)
    if idx < len([i for i in iterations if i['step'] != '...']) - 1 and step_num != '...':
        next_idx = idx + 1
        while next_idx < len(iterations) and iterations[next_idx]['step'] == '...':
            next_idx += 1

        if next_idx < len(iterations):
            next_y = step_y + iterations[next_idx]['y_offset']

            # Curved arrow back
            loop_arrow = FancyArrowPatch((pert_x_start + 6.4, current_y - 0.25),
                                        (pert_x_start + 2.6, next_y + 0.25),
                                        arrowstyle='->', mutation_scale=15, linewidth=2,
                                        color='#F57C00', connectionstyle="arc3,rad=0.3")
            ax.add_artist(loop_arrow)

            # Label on the loop
            mid_y = (current_y + next_y) / 2
            ax.text(pert_x_start + 7.2, mid_y, 'Use as\ninput', fontsize=6,
                   ha='center', va='center', style='italic', color='#E65100',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

# Key insight box
insight_box = FancyBboxPatch((pert_x_start + 0.5, final_y - 1.5), 6.5, 0.8,
                             boxstyle="round,pad=0.08",
                             edgecolor='#7B1FA2', facecolor=color_iteration, linewidth=3,
                             linestyle='--')
ax.add_patch(insight_box)
ax.text(pert_x_start + 3.75, final_y - 1.1, '🔄 KEY: Perturbation Applied at EVERY Step',
        fontsize=10, ha='center', fontweight='bold', color='#4A148C')
ax.text(pert_x_start + 3.75, final_y - 1.45,
        'Each iteration: Previous output → Add perturbation → Forecast next 6h → Export → Repeat',
        fontsize=7, ha='center', style='italic', color='#6A1B9A')

# ========== RIGHT SIDE: Output Analysis ==========
output_x = 13.5
output_y_start = 9.5

ax.text(output_x + 1.5, output_y_start + 0.5, 'OUTPUTS & ANALYSIS',
        fontsize=12, ha='center', fontweight='bold', color='#F57C00',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF3E0', edgecolor='#F57C00', linewidth=2))

# Variables collected
variables_y = output_y_start - 0.5
ax.text(output_x + 1.5, variables_y, 'Variables (28 steps):', fontsize=10, ha='center', fontweight='bold')

outputs = [
    {'name': 'Precipitation', 'icon': '💧', 'detail': '6-hr accumulation', 'color': '#BBDEFB'},
    {'name': '700 hPa Wind', 'icon': '🌪️', 'detail': 'From u, v components', 'color': color_700hpa},
    {'name': 'Temperature', 'icon': '🌡️', 'detail': 'Multiple levels', 'color': '#FFCCBC'},
    {'name': 'Other fields', 'icon': '📊', 'detail': 'Full atmospheric state', 'color': '#C5E1A5'},
]

for i, output in enumerate(outputs):
    out_y = variables_y - 0.8 - i * 0.7
    output_box = FancyBboxPatch((output_x, out_y), 3.0, 0.5,
                                boxstyle="round,pad=0.04",
                                edgecolor='#F57C00', facecolor=output['color'], linewidth=1.5)
    ax.add_patch(output_box)
    ax.text(output_x + 0.3, out_y + 0.25, output['icon'], fontsize=12, ha='center', va='center')
    ax.text(output_x + 1.5, out_y + 0.32, output['name'], fontsize=8, ha='center', va='top', fontweight='bold')
    ax.text(output_x + 1.5, out_y + 0.1, output['detail'], fontsize=6, ha='center', va='top', style='italic')

# Analysis methods
analysis_y = out_y - 1.0
ax.text(output_x + 1.5, analysis_y, 'Analysis:', fontsize=10, ha='center', fontweight='bold')

analysis_items = [
    'Control vs Perturbed',
    'Difference maps (95%ile scaled)',
    'Temporal evolution',
    'Butterfly effect quantification',
]

for i, item in enumerate(analysis_items):
    ax.text(output_x + 1.5, analysis_y - 0.35 - i * 0.25, f'• {item}',
            fontsize=7, ha='center')

# ========== BOTTOM: 700 hPa Emphasis ==========
hpa_y = 1.5

# Large emphasis box
hpa_emphasis = FancyBboxPatch((0.5, hpa_y - 0.8), 17.0, 1.2,
                              boxstyle="round,pad=0.1",
                              edgecolor='#7E57C2', facecolor=color_700hpa, linewidth=3,
                              alpha=0.3)
ax.add_patch(hpa_emphasis)

ax.text(9, hpa_y + 0.2, '🎯 700 hPa Level Focus', fontsize=14, ha='center', fontweight='bold', color='#4A148C')

hpa_reasons = [
    '✓ Jet stream dynamics (synoptic scale)',
    '✓ Mid-troposphere circulation',
    '✓ Better than 500 hPa for weather patterns',
    '✓ Crucial for precipitation systems',
    '✓ Perturbations: 700-925 hPa (ΔT from latent heat)',
]

for i, reason in enumerate(hpa_reasons):
    x_pos = 2.0 + (i * 3.4)
    ax.text(x_pos, hpa_y - 0.35, reason, fontsize=7, ha='left', va='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='#7E57C2'))

# Scientific goal at bottom
goal_text = ('Scientific Goal: Quantify sensitivity to initial conditions via iterative perturbations, '
            'assess predictability limits, and improve ensemble forecasting at synoptically-relevant levels')
ax.text(9, 0.3, goal_text, fontsize=8, ha='center', style='italic', color='#424242',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#EEEEEE', alpha=0.9, edgecolor='#666'))

# Save the figure
output_path = '/content/drive/MyDrive/Research/aurora-lite-decoder-perturbation/multiperturbation_diagram_v2.png'
plt.tight_layout()
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✓ Diagram v2 saved to: {output_path}")

# Also save as PDF
pdf_path = output_path.replace('.png', '.pdf')
plt.savefig(pdf_path, bbox_inches='tight', facecolor='white')
print(f"✓ PDF version saved to: {pdf_path}")

plt.close()

print("\n" + "="*70)
print("Iterative perturbation diagram successfully created!")
print("="*70)
print("\nKey features:")
print("  - Shows perturbation applied at EACH forecast step")
print("  - Illustrates the feedback loop: Output → Perturbation → Forecast")
print("  - Emphasizes 700 hPa level and iterative nature")
print("  - Clear visualization of control vs perturbed workflows")
