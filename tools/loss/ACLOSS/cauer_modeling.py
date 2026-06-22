"""
Cauer Ladder Circuit Modeling for AC Copper Loss (AC 동손) Estimation in PMSM Hairpin Windings.
Based on the Gemini conversation at https://gemini.google.com/share/19b8b2e98905.

This script:
1. Calculates Cauer ladder parameters (R and L values) for each stage of a conductor.
2. Computes the frequency-dependent input impedance (Z_in) of the Cauer network.
3. Estimates the AC resistance factor (Fr = Rac/Rdc) and AC inductance (Lac) as functions of frequency.
4. Optionally plots the AC resistance factor and inductance curves using Matplotlib.
"""

import numpy as np
import matplotlib.pyplot as plt

def calculate_cauer_parameters(d_cond, w_slot, sigma, l_core, num_turns=6, num_stages=3):
    """
    Calculates the Cauer ladder circuit parameters for hairpin windings.
    
    Parameters:
    - d_cond (float): Thickness (height) of a single hairpin conductor [m]
    - w_slot (float): Slot width [m]
    - sigma (float): Conductor conductivity [S/m]
    - l_core (float): Core stack length [m]
    - num_turns (int): Number of turns (hairpins) per slot (default: 6)
    - num_stages (int): Number of ladder stages per conductor (default: 3)
    
    Returns:
    - dict: A dictionary containing R_dc_total, Cauer_R_stages, and Cauer_L_stages
    """
    # 1. Physical Constant
    mu_0 = 4 * np.pi * 1e-7  # Vacuum permeability [H/m]
    
    # 2. Base Conductor Characteristics (based on Cauer network equations)
    L_c_base = mu_0 * d_cond / w_slot
    R_c_base = 8.0 / (sigma * d_cond * w_slot)
    
    # Scale with core stack length
    L_c = L_c_base * l_core
    R_c = R_c_base * l_core
    
    # 3. Calculate Cauer parameters per stage
    R_stages = []
    L_stages = []
    
    for k in range(1, num_stages + 1):
        l_coeff = 4 * k - 3
        L_k = L_c / l_coeff
        L_stages.append(L_k)
        
        r_coeff = 4 * k - 1
        R_k = r_coeff * R_c
        R_stages.append(R_k)
        
    # 4. Total DC Winding Resistance (for reference)
    r_dc_per_turn = 1.0 / (sigma * (d_cond * w_slot)) * l_core
    R_dc_total = r_dc_per_turn * num_turns

    return {
        "R_dc_total": R_dc_total,
        "R_dc_per_turn": r_dc_per_turn,
        "Cauer_R_stages": np.array(R_stages),
        "Cauer_L_stages": np.array(L_stages)
    }

def compute_input_impedance(freq, R_stages, L_stages):
    """
    Computes the input impedance Z_in(f) of the Cauer ladder network at a given frequency.
    
    The Cauer ladder network is represented as:
    ---[ R1 ]---+---[ R2 ]---+---[ R3 ]---+--- ... ---[ Rn ]---+
                |            |            |                    |
               (L1)         (L2)         (L3)                 (Ln)
                |            |            |                    |
    ------------+------------+------------+--- ... ------------+
    
    Parameters:
    - freq (float or np.ndarray): Frequency [Hz]
    - R_stages (np.ndarray): Array of resistance values for each stage [Ω]
    - L_stages (np.ndarray): Array of inductance values for each stage [H]
    
    Returns:
    - complex or np.ndarray: Input impedance Z_in [Ω]
    """
    omega = 2 * np.pi * freq
    num_stages = len(R_stages)
    
    # We compute the equivalent impedance from right (stage N) to left (stage 1)
    # Z_node[k] represents the impedance of the parallel combination of the shunt inductor L_k
    # and the series impedance looking into stage k+1.
    
    # Initialize the impedance looking into the right side of stage N (which is open / infinite impedance)
    # So the impedance at node N is just the impedance of the shunt inductor L_N
    Z_node = 1j * omega * L_stages[-1]
    
    # Iterate backwards from stage N-1 down to 1
    for k in range(num_stages - 2, -1, -1):
        Z_shunt = 1j * omega * L_stages[k]
        Z_right_branch = R_stages[k+1] + Z_node
        
        # Parallel combination of shunt inductor and right branch
        Z_node = 1.0 / (1.0 / Z_shunt + 1.0 / Z_right_branch)
        
    # Input impedance includes the first series resistor R_1
    Z_in = R_stages[0] + Z_node
    return Z_in

def analyze_frequency_response(params, freq_range):
    """
    Analyzes the AC resistance factor (Fr = Rac/Rdc) and AC inductance (Lac) over a frequency range.
    """
    R_stages = params["Cauer_R_stages"]
    L_stages = params["Cauer_L_stages"]
    R_dc_turn = params["R_dc_per_turn"]
    
    rac_list = []
    lac_list = []
    
    for f in freq_range:
        if f == 0:
            # DC behavior
            rac_list.append(R_dc_turn)
            lac_list.append(sum(L_stages))
        else:
            Z_in = compute_input_impedance(f, R_stages, L_stages)
            rac_list.append(Z_in.real)
            omega = 2 * np.pi * f
            lac_list.append(Z_in.imag / omega)
            
    rac_arr = np.array(rac_list)
    lac_arr = np.array(lac_list)
    fr_arr = rac_arr / R_dc_turn
    
    return fr_arr, lac_arr

if __name__ == "__main__":
    # Motor physical dimensions & materials (Example: 8-pole 48-slot hairpin winding motor)
    D_COND = 0.002      # 2 mm (height of conductor)
    W_SLOT = 0.006      # 6 mm (slot width)
    SIGMA = 5.8e7       # Copper conductivity at 20°C [S/m]
    L_CORE = 0.15       # 150 mm (stack length)
    TURNS = 6           # 6 turns per slot
    STAGES = 5          # 5-stage Cauer network for higher accuracy
    
    # 1. Calculate Cauer Parameters
    params = calculate_cauer_parameters(
        d_cond=D_COND, 
        w_slot=W_SLOT, 
        sigma=SIGMA, 
        l_core=L_CORE, 
        num_turns=TURNS, 
        num_stages=STAGES
    )
    
    print("==========================================================")
    print(" 8-Pole 48-Slot 6-Turn Hairpin Cauer Circuit Analysis")
    print("==========================================================")
    print(f"Total DC resistance per phase (slot approximation): {params['R_dc_total']:.6f} Ω")
    print(f"DC resistance per single turn: {params['R_dc_per_turn']:.6f} Ω")
    print("\nCalculated Cauer Parameters per Conductor (Turn):")
    for idx in range(STAGES):
        print(f"  Stage {idx+1}:")
        print(f"    - AC Resistance (R_{idx+1}): {params['Cauer_R_stages'][idx]:.6f} Ω")
        print(f"    - Eddy Inductance (L_{idx+1}): {params['Cauer_L_stages'][idx]*1e6:.4f} μH")
    print("==========================================================")

    # 2. Analyze frequency response (0 Hz to 5 kHz)
    freqs = np.linspace(0, 5000, 500)
    fr_factors, lac_values = analyze_frequency_response(params, freqs)
    
    print(f"\nFrequency Response Summary:")
    print(f"  At 100 Hz  -> Fr (Rac/Rdc): {fr_factors[np.abs(freqs - 100).argmin()]:.4f}")
    print(f"  At 500 Hz  -> Fr (Rac/Rdc): {fr_factors[np.abs(freqs - 500).argmin()]:.4f}")
    print(f"  At 1000 Hz -> Fr (Rac/Rdc): {fr_factors[np.abs(freqs - 1000).argmin()]:.4f}")
    print(f"  At 2000 Hz -> Fr (Rac/Rdc): {fr_factors[np.abs(freqs - 2000).argmin()]:.4f}")
    print(f"  At 5000 Hz -> Fr (Rac/Rdc): {fr_factors[np.abs(freqs - 5000).argmin()]:.4f}")
    
    # 3. Plotting
    try:
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        color = 'tab:red'
        ax1.set_xlabel('Frequency (Hz)', fontsize=12)
        ax1.set_ylabel('AC Resistance Factor (Fr = Rac / Rdc)', color=color, fontsize=12)
        line1 = ax1.plot(freqs, fr_factors, color=color, linewidth=2.5, label='AC Resistance Factor (Fr)')
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.grid(True, linestyle='--', alpha=0.6)
        
        ax2 = ax1.twinx()  
        color = 'tab:blue'
        ax2.set_ylabel('AC Equivalent Inductance (μH)', color=color, fontsize=12)
        line2 = ax2.plot(freqs, lac_values * 1e6, color=color, linestyle='--', linewidth=2, label='AC Inductance (Lac)')
        ax2.tick_params(axis='y', labelcolor=color)
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left')
        
        plt.title('Frequency-Dependent Winding Impedance (Cauer Ladder Model)', fontsize=14, fontweight='bold', pad=15)
        fig.tight_layout()
        
        # Save the plot as a PNG artifact in the workspace
        plot_path = "/Users/kdh2021-air/Library/CloudStorage/GoogleDrive-phareal87@gmail.com/내 드라이브/ACloss/cauer_frequency_response.png"
        plt.savefig(plot_path, dpi=300)
        print(f"\nPlot saved successfully to: {plot_path}")
        plt.close()
    except Exception as e:
        print(f"\nCould not generate plot: {e}")
