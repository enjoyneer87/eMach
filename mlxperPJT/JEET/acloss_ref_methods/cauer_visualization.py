"""
Cauer Ladder Circuit Schematic Drawing Module using Matplotlib.
Designed for PMSM Hairpin Winding AC Copper Loss Analysis.
"""

import numpy as np
import matplotlib.pyplot as plt

def draw_resistor(ax, x_start, x_end, y0, color='#D35400', num_zigzags=5, height=0.15):
    """Draws a horizontal zigzag resistor symbol."""
    # Wire lead lines
    lead_len = 0.35
    ax.plot([x_start, x_start + lead_len], [y0, y0], color='#2C3E50', lw=2)
    ax.plot([x_end - lead_len, x_end], [y0, y0], color='#2C3E50', lw=2)
    
    # Zigzag points
    x_res_start = x_start + lead_len
    x_res_end = x_end - lead_len
    w = x_res_end - x_res_start
    
    pts = 2 * num_zigzags + 1
    x_pts = np.linspace(x_res_start, x_res_end, pts + 2)
    y_pts = np.zeros_like(x_pts) + y0
    
    for i in range(1, pts + 1):
        y_pts[i] = y0 + height if i % 2 == 1 else y0 - height
        
    ax.plot(x_pts, y_pts, color=color, lw=2.5)

def draw_inductor(ax, x0, y_start, y_end, color='#2980B9', num_loops=4, r_x=0.12, r_y=0.04):
    """Draws a vertical coil inductor symbol."""
    # Wire lead lines
    lead_len = 0.25
    ax.plot([x0, x0], [y_start, y_start - lead_len], color='#2C3E50', lw=2)
    ax.plot([x0, x0], [y_end + lead_len, y_end], color='#2C3E50', lw=2)
    
    # Coil points
    y_coil_start = y_start - lead_len
    y_coil_end = y_end + lead_len
    h = y_coil_start - y_coil_end
    
    t = np.linspace(0, num_loops * 2 * np.pi, 300)
    y_pts = y_coil_start - (t / (num_loops * 2 * np.pi)) * h + r_y * (np.cos(t) - 1)
    x_pts = x0 + r_x * np.sin(t)
    
    ax.plot(x_pts, y_pts, color=color, lw=2.5)

def draw_ground(ax, x, y, color='#2C3E50'):
    """Draws a standard ground symbol."""
    ax.plot([x, x], [y, y - 0.15], color=color, lw=2)
    ax.plot([x - 0.2, x + 0.2], [y - 0.15, y - 0.15], color=color, lw=2)
    ax.plot([x - 0.12, x + 0.12], [y - 0.22, y - 0.22], color=color, lw=2)
    ax.plot([x - 0.05, x + 0.05], [y - 0.29, y - 0.29], color=color, lw=2)

def draw_cauer_schematic(params, save_path=None):
    """
    Draws a highly polished schematic diagram of the Cauer ladder network.
    
    Parameters:
    - params (dict): Dictionary containing Cauer_R_stages and Cauer_L_stages.
    - save_path (str): File path to save the generated figure.
    
    Returns:
    - fig, ax: Matplotlib figure and axis objects.
    """
    R_stages = params["Cauer_R_stages"]
    L_stages = params["Cauer_L_stages"]
    num_stages = len(R_stages)
    
    # Calculate figure dimensions dynamically based on stages
    fig_w = max(10, num_stages * 2.5)
    fig_h = 5
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
    
    # Set plot bounds and clear axes
    ax.set_xlim(-1, num_stages * 2.2 + 1)
    ax.set_ylim(-0.8, 3.2)
    ax.set_aspect('equal')
    ax.axis('off')
    
    W = 2.2  # Stage width
    y_top = 2.0
    y_bottom = 0.0
    
    # Draw Ground Wires & Nodes
    ax.plot([0, num_stages * W], [y_bottom, y_bottom], color='#2C3E50', lw=2)
    
    # Draw Input Terminals
    ax.plot([-0.5, 0], [y_top, y_top], color='#2C3E50', lw=2)
    ax.plot([-0.5, 0], [y_bottom, y_bottom], color='#2C3E50', lw=2)
    
    ax.plot(-0.5, y_top, marker='o', color='#2C3E50', markersize=8, fillstyle='none', mew=2)
    ax.plot(-0.5, y_bottom, marker='o', color='#2C3E50', markersize=8, fillstyle='none', mew=2)
    
    ax.text(-0.8, y_top, "In (+)", fontsize=11, fontweight='bold', va='center', ha='right', color='#2C3E50')
    ax.text(-0.8, y_bottom, "Ref (-)", fontsize=11, fontweight='bold', va='center', ha='right', color='#2C3E50')
    
    # Draw each stage
    for k in range(num_stages):
        x_start = k * W
        x_end = (k + 1) * W
        
        # 1. Series Resistor
        draw_resistor(ax, x_start, x_end, y_top, color='#D35400')
        
        # Resistor Label & Value
        r_val = R_stages[k]
        r_label = f"$R_{{{k+1}}}$\n"
        if r_val < 1.0:
            r_label += f"{r_val * 1e3:.3f} m$\\Omega$"
        else:
            r_label += f"{r_val:.4f} $\\Omega$"
            
        ax.text((x_start + x_end)/2, y_top + 0.35, r_label, 
                fontsize=10, ha='center', va='bottom', color='#D35400', fontweight='semibold')
        
        # 2. Shunt Inductor
        draw_inductor(ax, x_end, y_top, y_bottom, color='#2980B9')
        
        # Inductor Label & Value
        l_val = L_stages[k]
        l_label = f"$L_{{{k+1}}}$: "
        if l_val < 1e-6:
            l_label += f"{l_val * 1e6:.3f} $\\mu$H"
        else:
            l_label += f"{l_val * 1e3:.3f} mH"
            
        ax.text(x_end + 0.2, (y_top + y_bottom)/2, l_label, 
                fontsize=10, ha='left', va='center', color='#2980B9', fontweight='semibold')
        
        # 3. Connection Nodes (dots)
        ax.plot([x_end], [y_top], marker='o', color='#2C3E50', markersize=6)
        ax.plot([x_end], [y_bottom], marker='o', color='#2C3E50', markersize=6)
        
    # Draw Ground Symbol at the bottom left (Ref node)
    draw_ground(ax, 0.0, y_bottom, color='#2C3E50')
    
    # Title
    ax.text(num_stages * W / 2, 2.9, f"Cauer Ladder Equivalent Winding Model ({num_stages}-Stage)", 
            fontsize=13, fontweight='bold', ha='center', color='#2C3E50')
    
    # Add a legend-like card at the bottom right
    # (Optional box indicating Hairpin Winding modeling parameters)
    props = dict(boxstyle='round,pad=0.5', facecolor='#F8F9F9', edgecolor='#BDC3C7', alpha=0.9)
    ax.text(num_stages * W, -0.4, "Eddy Current Ladder Network", 
            fontsize=9, style='italic', ha='right', va='top', bbox=props, color='#7F8C8D')

    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
    return fig, ax
