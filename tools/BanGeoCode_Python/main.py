import numpy as np
import matplotlib.pyplot as plt
from Geometry import generate_geometry
from Feasibility import check_feasibility
import time

def Rnd(range_val, N):
    """
    Generate N random numbers within range_val [min, max].
    If range_val has 1 element, return that element repeated N times.
    """
    range_val = np.array(range_val)
    if len(range_val) > 1:
        return (range_val[1] - range_val[0]) * np.random.rand(N) + range_val[0]
    else:
        return np.full(N, range_val[0])

def main():
    n_iteration = 1
    n_feasible = 0
    max_feasible_designs = 1 # How many feasible designs to find
    
    print("Starting Random Geometry Generation...")
    
    while n_feasible < max_feasible_designs:
        # Machine Parameters
        params = {}
        params['VMagnet_Layers'] = 2
        params['Pole_Number'] = 8
        params['Shaft_Dia'] = 75
        params['Slot_Number'] = 48
        params['Stator_Lam_Dia'] = 230
        params['Airgap'] = 0.71
        params['Shaft_Hole_Diameter'] = 0
        
        # Random Split Ratio
        split_ratio = Rnd([0.7, 0.8], 1)[0]
        params['Stator_Bore'] = round(split_ratio * params['Stator_Lam_Dia'], 1)
        
        lay = params['VMagnet_Layers']
        
        # Optimization variables
        params['MagnetThickness_Array'] = Rnd([2, 6], lay)
        
        # VSimpleWidth_Array: [Rnd([10 15],1) Rnd([15 20],1)]
        w1 = Rnd([10, 15], 1)[0]
        w2 = Rnd([15, 20], 1)[0]
        params['VSimpleWidth_Array'] = np.array([w1, w2])
        
        params['VSimpleMagShift_Array'] = Rnd([0, 0], lay)
        
        # MagnetBarWidth_Array
        factor = Rnd([0.5, 1], 1)[0]
        params['MagnetBarWidth_Array'] = factor * params['VSimpleWidth_Array']
        
        # BridgeThickness_Array
        b1 = Rnd([1, 2], 1)[0]
        b2 = Rnd([10, 15], 1)[0]
        params['BridgeThickness_Array'] = np.array([b1, b2])
        
        # PoleVAngle_Array
        a1 = Rnd([120, 180], 1)[0]
        a2 = Rnd([100, 150], 1)[0]
        params['PoleVAngle_Array'] = np.array([a1, a2])
        
        params['VSimpleEndRegion_Outer_Array'] = Rnd([1, 1], lay)
        params['VSimpleEndRegion_Inner_Array'] = Rnd([1, 1], lay)
        params['VSimpleMagnetPost_Array'] = Rnd([0.1, 3], lay)
        params['VShape_Magnet_ClearanceOuter'] = Rnd([0, 0], lay)
        params['VShape_Magnet_ClearanceInner'] = Rnd([0, 0], lay)
        
        params['PoleNotchDepth'] = Rnd([1, 10], 1)[0]
        params['PoleNotchArc_Inner'] = Rnd([5, 20], 1)[0]
        params['PoleNotchArc_Outer'] = 1.2 * params['PoleNotchArc_Inner']
        
        params['r_10'] = Rnd([0, 1], 1)[0]
        params['r_11'] = Rnd([0, 1], 1)[0]
        params['r_M'] = 0.2
        
        try:
            shapes = generate_geometry(params)
            
            symmetry_angle = 360.0 / params['Pole_Number'] / 2.0
            is_feasible = check_feasibility(shapes, symmetry_angle)
            
            if is_feasible:
                print(f"Iteration {n_iteration}: PASS")
                n_feasible += 1
                
                # Plotting
                fig, ax = plt.subplots(figsize=(8, 8))
                for shape in shapes:
                    shape.plot(ax=ax)
                ax.set_aspect('equal')
                ax.set_title(f"Iteration {n_iteration} - PASS")
                plt.grid(True)
                plt.show()
                
            else:
                print(f"Iteration {n_iteration}: FAIL")
                
        except Exception as e:
            print(f"Iteration {n_iteration}: Error - {e}")
            # import traceback
            # traceback.print_exc()
        
        n_iteration += 1
        if n_iteration > 1000: # Safety break
            print("Max iterations reached.")
            break

if __name__ == "__main__":
    main()
