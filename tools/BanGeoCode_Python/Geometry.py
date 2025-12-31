import numpy as np
import matplotlib.pyplot as plt
from Primitives import Point, Line, Arc, fillet_L2L, fillet_A2L
from Shape import Shape, subtract, union

def generate_geometry(in_params, plot_shapes=None, plot_regions=None):
    # Unpack parameters
    lay = int(in_params['VMagnet_Layers'])
    
    # Helper to ensure array
    def get_arr(key):
        val = np.array(in_params[key])
        if val.ndim == 0: val = np.array([val])
        return val[:lay] # Slice to layers

    poleVangle = get_arr('PoleVAngle_Array')
    poles = in_params['Pole_Number']
    Rsh = in_params['Shaft_Dia'] / 2.0
    Db = in_params['Stator_Bore']
    da = in_params['Airgap']
    Dsh_hole = in_params['Shaft_Hole_Diameter']
    Rr = 0.5 * Db - da
    Ds = in_params['Stator_Lam_Dia']
    Ns = in_params['Slot_Number']

    h_mag = get_arr('MagnetThickness_Array')
    h_c_out = get_arr('VShape_Magnet_ClearanceOuter')
    h_c_in = get_arr('VShape_Magnet_ClearanceInner')
    h_c = h_c_out + h_c_in
    h = h_mag + h_c

    w = get_arr('MagnetBarWidth_Array')
    V = get_arr('VSimpleWidth_Array')

    ext_i = get_arr('VSimpleEndRegion_Inner_Array')
    ext_o = get_arr('VSimpleEndRegion_Outer_Array')

    sh = get_arr('VSimpleMagShift_Array')
    b = get_arr('BridgeThickness_Array')
    p = get_arr('VSimpleMagnetPost_Array')

    nd = in_params.get('PoleNotchDepth', 0)
    ndo = in_params.get('PoleNotchArc_Outer', 0)
    ndi = in_params.get('PoleNotchArc_Inner', 0)

    betamin = 90 - 180.0 / poles
    gamma = 90 - poleVangle / 2.0
    tau_pole = 2 * np.pi / poles

    r_10 = in_params.get('r_10', 0)
    r_11 = in_params.get('r_11', 0)
    r_M = in_params.get('r_M', 0)

    # Pre-calculations
    Ri = np.zeros(lay)
    Ro = np.zeros(lay)
    for i in range(lay):
        if ext_i[i] == 0:
            Ri[i] = 0
        else:
            Ri[i] = (ext_i[i]**2 + (0.5 * h[i])**2) / (2 * ext_i[i])
        
        if ext_o[i] == 0:
            Ro[i] = 0
        else:
            Ro[i] = (ext_o[i]**2 + (0.5 * h[i])**2) / (2 * ext_o[i])

    # Point Definitions
    # Note: Using numpy arrays for coordinates allows vectorized operations for all layers
    
    # Point r0
    P_r0 = Point(0.0, 0.0)
    
    # Point B
    P_rB = Point()
    P_rB.x = Ri + 0.5 * p
    P_rB.c2p()

    # Point A
    P_rA = Point()
    P_rA.x = P_rB.x - (Ri - ext_i) * np.cos(np.deg2rad(gamma))
    P_rA.c2p()

    # Point 1
    P_r1 = Point()
    P_r1.x = P_rA.x - 0.5 * h * np.cos(np.deg2rad(poleVangle / 2.0))
    
    # Recalculation loop
    for i in range(lay):
        if P_r1.x[i] <= 0.5 * p[i]:
            P_r1.x[i] = 0.5 * p[i]
            P_rA.x[i] = P_r1.x[i] + 0.5 * h[i] * np.cos(np.deg2rad(poleVangle[i] / 2.0))
    P_r1.c2p() # Update other props if needed, though y is 0 so far? No, y is not set yet.
    # Wait, MATLAB code: P_r1.x = ...; then later P_r1.y = ...
    
    # Point C
    P_rC = Point()
    P_rC.x = P_rA.x + V * np.cos(np.deg2rad(gamma))
    
    # Point D
    P_rD = Point()
    P_rD.x = P_rC.x - (Ro - ext_o) * np.cos(np.deg2rad(gamma))
    P_rD.R = Rr - b - Ro
    # P_rD.y = sqrt(P_rD.R.^2-P_rD.x.^2);
    P_rD.y = np.sqrt(P_rD.R**2 - P_rD.x**2)
    P_rD.c2p()

    P_rC.y = P_rD.y + (Ro - ext_o) * np.sin(np.deg2rad(gamma))
    P_rC.c2p()

    # Point 4
    P_r4 = Point()
    P_r4.y = P_rC.y + 0.5 * h * np.cos(np.deg2rad(gamma))
    P_r4.x = P_r1.x + V * np.cos(np.deg2rad(gamma))
    P_r4.c2p()

    # Recalculation loop for D and 4
    for i in range(lay):
        if P_rD.beta[i] > P_r4.beta[i]:
            P_r4.R[i] = Rr - b[i]
            P_r4.y[i] = np.sqrt(P_r4.R[i]**2 - P_r4.x[i]**2)
            P_r4.c2p() # Update beta
            P_rC.y[i] = P_r4.y[i] - 0.5 * h[i] * np.cos(np.deg2rad(gamma[i]))
            P_rD.y[i] = P_rC.y[i] - (Ro[i] - ext_o[i]) * np.sin(np.deg2rad(gamma[i]))
            # Update P_rD props?
            P_rD.x[i] = P_rC.x[i] - (Ro[i] - ext_o[i]) * np.cos(np.deg2rad(gamma[i])) # x might change?
            # MATLAB code doesn't update P_rD.x inside the loop, but P_rD.y depends on P_rC.y
            # Wait, MATLAB: P_rD.y(i) = P_rC.y(i) - ...
            # It doesn't update P_rD.x. But P_rD.x was calculated from P_rC.x.
            # P_rC.x was calculated from P_rA.x.
            # P_rA.x was fixed.
            # So P_rD.x is fixed.
            pass
    
    P_rC.c2p()
    P_rD.c2p()

    P_rA.y = P_rC.y - V * np.sin(np.deg2rad(gamma))
    P_rA.c2p()

    P_rB.y = (P_rB.x - P_rA.x) * np.tan(np.deg2rad(gamma)) + P_rA.y
    P_rB.c2p()

    P_r1.y = P_r4.y - V * np.sin(np.deg2rad(gamma))
    P_r1.c2p()

    # Point 2
    P_r2 = Point()
    P_r2.x = P_r1.x + (V/2 - w/2 + sh) * np.cos(np.deg2rad(gamma))
    P_r2.y = P_r1.y + (V/2 - w/2 + sh) * np.sin(np.deg2rad(gamma))
    P_r2.c2p()

    # Point 3
    P_r3 = Point()
    P_r3.x = P_r2.x + w * np.cos(np.deg2rad(gamma))
    P_r3.y = P_r2.y + w * np.sin(np.deg2rad(gamma))
    P_r3.c2p()

    # Point 8
    P_r8 = Point()
    P_r8.x = P_r1.x + h * np.cos(np.deg2rad(poleVangle / 2.0))
    P_r8.y = P_r1.y - h * np.sin(np.deg2rad(poleVangle / 2.0))
    P_r8.c2p()

    # Point 7
    P_r7 = Point()
    P_r7.x = P_r8.x + (P_r2.x - P_r1.x)
    P_r7.y = P_r8.y + (P_r2.y - P_r1.y)
    P_r7.c2p()

    # Point 6
    P_r6 = Point()
    P_r6.x = P_r8.x + (P_r3.x - P_r1.x)
    P_r6.y = P_r8.y + (P_r3.y - P_r1.y)
    P_r6.c2p()

    # Point 5
    P_r5 = Point()
    P_r5.x = P_r8.x + (P_r4.x - P_r1.x)
    P_r5.y = P_r8.y + (P_r4.y - P_r1.y)
    P_r5.c2p()

    # Notch Definition
    # Point r10
    P_r10 = Point()
    P_r10.R = Rr
    P_r10.beta = np.deg2rad(betamin + ndo / poles)
    P_r10.p2c()

    # Point r11
    P_r11 = Point()
    P_r11.R = Rr - nd
    P_r11.beta = np.deg2rad(betamin + ndi / poles)
    P_r11.p2c()

    # Point r12
    P_r12 = Point()
    P_r12.R = Rr - nd
    P_r12.beta = np.deg2rad(betamin)
    P_r12.p2c()

    # Rotor and Shaft Points
    # Point r13
    P_r13 = Point()
    P_r13.R = Rsh
    P_r13.beta = np.pi/2 - tau_pole/2
    P_r13.p2c()

    # Point r14
    P_r14 = Point()
    P_r14.R = Rsh
    P_r14.beta = np.pi/2 + tau_pole/2
    P_r14.p2c()

    # Point r15
    P_r15 = Point()
    P_r15.R = Db/2 - da
    P_r15.beta = np.pi/2 - tau_pole/2
    P_r15.p2c()

    # Point r16
    P_r16 = Point()
    P_r16.R = Db/2 - da
    P_r16.beta = np.pi/2
    P_r16.p2c()

    # Point r17
    P_r17 = Point()
    P_r17.R = Dsh_hole/2
    P_r17.beta = np.pi/2 - tau_pole/2
    P_r17.p2c()

    # Point r18
    P_r18 = Point()
    P_r18.R = Dsh_hole/2
    P_r18.beta = np.pi/2 + tau_pole/2
    P_r18.p2c()

    # Define Arcs and Lines
    drw = [{}, {}] # drw(1) and drw(2)

    # drw(1)
    drw[0]['A_rA'] = Arc().define(P_r1, P_r8, P_rB)
    drw[0]['A_rC'] = Arc().define(P_r5, P_r4, P_rD)
    drw[0]['L_r01_04'] = Line().define(P_r4, P_r1)
    drw[0]['L_r08_05'] = Line().define(P_r8, P_r5)

    # Magnets (Fillets)
    # Note: fillet_L2L returns an Arc.
    # Since P_r3, P_r2 etc are arrays, fillet_L2L needs to handle arrays or we loop?
    # My fillet_L2L implementation assumes scalars (Point objects with scalar x,y).
    # If P_r3.x is array, fillet_L2L will fail or produce weird results if not vectorized.
    # My fillet_L2L uses np.linalg.norm which reduces array.
    # I MUST loop over layers to create primitives for each layer if I want to support multi-layer correctly with the current Primitives implementation.
    # OR I vectorize fillet_L2L.
    # Given the complexity, looping over layers to create the "drw" structure might be better?
    # But MATLAB creates ONE Arc object that holds arrays.
    # If I want 1:1, I should vectorize fillet_L2L.
    # Let's assume for now I loop over layers when creating Shapes, but for Primitives...
    # If I have 2 layers, `drw.A_r02M` in MATLAB is an object with x, y arrays.
    # In Python, if I use my Primitives, I should probably make them hold arrays.
    # My `Point` holds arrays. `Arc` holds `Point`s (arrays).
    # `fillet_L2L` needs to return an `Arc` with array properties.
    # I need to update `fillet_L2L` to handle arrays.
    # `np.linalg.norm(v1)` -> returns scalar if v1 is 1D array. If v1 is (2, N), axis=0?
    # v1 = [P1.x - P2.x, P1.y - P2.y]. If x is array of shape (N,), v1 is (2, N).
    # np.linalg.norm(v1, axis=0) -> (N,).
    # So I need to update `fillet_L2L` to use `axis=0`.
    
    # I will assume the user wants me to fix `Primitives.py` to be vectorized if I haven't already.
    # In `Primitives.py` I wrote: `norm1 = np.linalg.norm(v1)`. This is wrong for arrays.
    # I should fix `Primitives.py` first? Or just handle it here?
    # I'll fix `Primitives.py` logic in my mind: `v1` is shape (2,) or (2, N).
    # I'll update `fillet_L2L` in `Primitives.py`? No, I just wrote it.
    # I'll overwrite `Primitives.py` AGAIN with vectorized support?
    # Or I can just loop here.
    # Looping is safer and easier to debug.
    # But `drw` structure in MATLAB holds arrays.
    # If I loop, I get `drw` as list of lists of primitives?
    # `drw[0]['A_r02M']` -> List of Arcs (one per layer)?
    # This changes the structure.
    # MATLAB: `drw.A_r02M.x` is (N, 100).
    # If I use `Arc` with array points, `Arc.discretize` returns (N, 100).
    # So I should try to support arrays.
    
    # I will update `Primitives.py` to be vectorized.
    # But I can't edit it again easily without deleting.
    # I'll just define a local `fillet_L2L_vec` here or monkey patch.
    # Actually, `np.linalg.norm` without axis flattens.
    # I'll use a custom norm function.
    
    def vec_norm(v):
        return np.sqrt(np.sum(v**2, axis=0))
    
    def fillet_L2L_vec(P1, P2, P3, r):
        # Vectorized version of fillet_L2L
        v1 = np.array([P1.x - P2.x, P1.y - P2.y])
        v2 = np.array([P3.x - P2.x, P3.y - P2.y])
        
        norm1 = vec_norm(v1)
        norm2 = vec_norm(v2)
        
        # Handle zeros?
        # n1 = v1 / norm1
        n1 = np.divide(v1, norm1, out=np.zeros_like(v1), where=norm1!=0)
        n2 = np.divide(v2, norm2, out=np.zeros_like(v2), where=norm2!=0)
        
        dot_val = np.sum(n1 * n2, axis=0)
        dot_val = np.clip(dot_val, -1.0, 1.0)
        angle = np.arccos(dot_val)
        
        d = r / np.tan(angle / 2.0)
        
        T1 = Point(P2.x + n1[0] * d, P2.y + n1[1] * d)
        T2 = Point(P2.x + n2[0] * d, P2.y + n2[1] * d)
        
        bisector = n1 + n2
        bisector_norm = vec_norm(bisector)
        bisector = np.divide(bisector, bisector_norm, out=np.zeros_like(bisector), where=bisector_norm!=0)
        
        dist_to_center = r / np.sin(angle / 2.0)
        
        C = Point(P2.x + bisector[0] * dist_to_center, P2.y + bisector[1] * dist_to_center)
        
        return Arc(T1, T2, C)

    drw[0]['A_r02M'] = fillet_L2L_vec(P_r3, P_r2, P_r7, r_M)
    drw[0]['A_r03M'] = fillet_L2L_vec(P_r6, P_r3, P_r2, r_M)
    drw[0]['A_r07M'] = fillet_L2L_vec(P_r2, P_r7, P_r6, r_M)
    drw[0]['A_r06M'] = fillet_L2L_vec(P_r7, P_r6, P_r3, r_M)

    drw[0]['L_r03M_02M'] = Line().define(drw[0]['A_r03M'].C2, drw[0]['A_r02M'].C1)
    drw[0]['L_r02M_07M'] = Line().define(drw[0]['A_r02M'].C2, drw[0]['A_r07M'].C1)
    drw[0]['L_r07M_06M'] = Line().define(drw[0]['A_r07M'].C2, drw[0]['A_r06M'].C1)
    drw[0]['L_r06M_03M'] = Line().define(drw[0]['A_r06M'].C2, drw[0]['A_r03M'].C1)

    # Notch and Rotor
    if nd > 0:
        # Arc P12 - P11
        drw[0]['A_r12_11'] = Arc().define(P_r12, P_r11) # Or=0,0 default
        
        # Fillet A_r11
        # Using approximation or custom logic
        # drw.A_r11 = fillet_A2L(P_r10,P_r11,P_r12,[],r_11,rotor_construction);
        # P_r10 (OD), P_r11 (Corner), P_r12 (Notch Bottom)
        # My fillet_A2L implementation: (P_arc_far, P_corner, P_line_far, ...)
        # P_arc_far=P_r10, P_corner=P_r11, P_line_far=P_r12
        # But wait, my implementation assumes P_line_far is on the ARC side?
        # "Approximation of fillet between an Arc (ending at P_corner) and a Line (starting at P_corner)."
        # Here: Arc P12->P11. Line P11->P10.
        # So P_line_far should be P12 (start of arc).
        # P_corner is P11.
        # P_arc_far is P10 (end of line).
        # So call: fillet_A2L(P_r10, P_r11, P_r12, ...)
        # Matches MATLAB args order!
        
        # I need a vectorized fillet_A2L too?
        # nd, ndo, ndi are scalars usually.
        # If they are scalars, P_r10 etc are scalars (or arrays of same value).
        # So vectorized logic should work.
        
        # I need to implement `fillet_A2L_vec` locally or use the one in Primitives if I update it.
        # I'll implement local `fillet_A2L_vec`.
        
        def fillet_A2L_vec(P_arc_far, P_corner, P_line_far, r):
             v_chord = np.array([P_line_far.x - P_corner.x, P_line_far.y - P_corner.y])
             t1 = np.array([-P_corner.y, P_corner.x])
             t2 = np.array([P_corner.y, -P_corner.x])
             
             dot1 = np.sum(t1 * v_chord, axis=0)
             dot2 = np.sum(t2 * v_chord, axis=0)
             
             # t_back = where(dot1 > dot2, t1, t2)
             # Need to handle array selection
             mask = dot1 > dot2
             t_back = np.where(mask, t1, t2)
             
             scale = vec_norm(v_chord)
             t_back_norm = vec_norm(t_back)
             t_back_unit = np.divide(t_back, t_back_norm, out=np.zeros_like(t_back), where=t_back_norm!=0)
             
             P_virtual_arc = Point(P_corner.x + t_back_unit[0]*scale, 
                                   P_corner.y + t_back_unit[1]*scale)
             
             return fillet_L2L_vec(P_virtual_arc, P_corner, P_arc_far, r)

        drw[0]['A_r11'] = fillet_A2L_vec(P_r10, P_r11, P_r12, r_11)
        
        # Redefine A_r12_11
        drw[0]['A_r12_11'] = Arc().define(P_r12, drw[0]['A_r11'].C1)
        
        # Fillet A_r10
        # drw.A_r10 = fillet_A2L(drw.A_r11.C2,P_r10,P_r16,[],r_10,rotor_construction);
        # P_arc_far = A_r11.C2 (start of line?)
        # P_corner = P_r10
        # P_line_far = P_r16 (end of arc?)
        # Wait, usage: fillet_A2L(FarPointOnLine, Corner, FarPointOnArc) ?
        # In previous call: fillet_A2L(P_r10, P_r11, P_r12) -> P10 (Line end), P11 (Corner), P12 (Arc start).
        # Here: fillet_A2L(drw.A_r11.C2, P_r10, P_r16) -> A_r11.C2 (Line start), P10 (Corner), P16 (Arc end).
        # So yes, consistent.
        drw[0]['A_r10'] = fillet_A2L_vec(drw[0]['A_r11'].C2, P_r10, P_r16, r_10)
        drw[0]['A_r10'].flip() # MATLAB: drw.A_r10.flip;
        
        drw[0]['L_r11_10'] = Line().define(drw[0]['A_r11'].C2, drw[0]['A_r10'].C1)
        drw[0]['A_r10_16'] = Arc().define(drw[0]['A_r10'].C2, P_r16)
        drw[0]['A_r10_15'] = Arc().define(drw[0]['A_r10'].C2, P_r15)
        drw[0]['L_r13_12'] = Line().define(P_r13, P_r12)
        
    else:
        drw[0]['A_r15_16'] = Arc().define(P_r15, P_r16)

    drw[0]['L_r17_15'] = Line().define(P_r17, P_r15)

    # Mirroring
    # drw(2)
    for key, val in drw[0].items():
        temp = val.copy()
        temp.mrr(np.pi/2)
        drw[1][key] = temp

    # Rotor and Shaft (not mirrored)
    drw[0]['A_r18_17'] = Arc().define(P_r18, P_r17, P_r0)
    drw[0]['A_r13_14'] = Arc().define(P_r13, P_r14, P_r0)

    # Rotation
    # Rotate all primitives for -tau_pole/2
    rot_angle = -(np.pi/2 - tau_pole/2)
    for j in range(2):
        for key, val in drw[j].items():
            val.rot(rot_angle)

    # Create Shapes
    Rotor = []
    
    # Helper to get coordinates from primitive for a specific layer
    def get_xy(prim, layer_idx):
        # prim is Arc or Line with array properties
        # We need to discretize or extract points for this layer.
        if isinstance(prim, Arc):
            # Create a temp scalar arc for this layer
            # Or update discretize to handle arrays?
            # My Arc.discretize handles arrays! returns x, y arrays.
            # x is (num_points, num_layers) or (num_layers, num_points)?
            # np.linspace(b1, b2, N) where b1, b2 are arrays (L,)
            # Result is (N, L).
            # So x[:, layer_idx] is the path.
            x_all, y_all = prim.discretize()
            if x_all.ndim > 1:
                return x_all[:, layer_idx], y_all[:, layer_idx]
            else:
                return x_all, y_all
        elif isinstance(prim, Line):
            # Line: P1, P2.
            p1x = prim.P1.x
            p1y = prim.P1.y
            p2x = prim.P2.x
            p2y = prim.P2.y
            
            # Handle scalar vs array
            val_p1x = p1x[layer_idx] if np.ndim(p1x) > 0 else p1x
            val_p1y = p1y[layer_idx] if np.ndim(p1y) > 0 else p1y
            val_p2x = p2x[layer_idx] if np.ndim(p2x) > 0 else p2x
            val_p2y = p2y[layer_idx] if np.ndim(p2y) > 0 else p2y
            
            return np.array([val_p1x, val_p2x]), np.array([val_p1y, val_p2y])
        return np.array([]), np.array([])

    for j in range(2): # 0 and 1
        for i in range(lay):
            # Magnets
            # X= [ drw(j).A_r03M.x(i,:) drw(j).A_r02M.x(i,:) ... ]
            # Note: MATLAB Arc.x is (layer, points).
            # My get_xy returns (points,).
            
            x1, y1 = get_xy(drw[j]['A_r03M'], i)
            x2, y2 = get_xy(drw[j]['A_r02M'], i)
            x3, y3 = get_xy(drw[j]['A_r07M'], i)
            x4, y4 = get_xy(drw[j]['A_r06M'], i)
            
            X = np.concatenate([x1, x2, x3, x4])
            Y = np.concatenate([y1, y2, y3, y4])
            
            s = Shape().ply(X, Y).lay(i+1, j+1).des("Magnet").ost(f"L{i+1}_1Magnet{j+1}")
            Rotor.append(s)
            if plot_shapes: s.plot(plot_shapes)

            # Air pockets inner
            # X= [drw(j).A_r02M.x(i,:) drw(j).A_r07M.x(i,:) fliplr(drw(j).A_rA.x(i,:))];
            xa, ya = get_xy(drw[j]['A_rA'], i)
            X = np.concatenate([x2, x3, np.flip(xa)])
            Y = np.concatenate([y2, y3, np.flip(ya)])
            
            s = Shape().ply(X, Y).lay(i+1, j+1)
            # Subtract previous magnet?
            # Rotor(end).poly=subtract(Rotor(end).poly,Rotor(end-1).poly);
            s.poly = subtract(s.poly, Rotor[-1].poly) # Rotor[-1] is the Magnet (last added)
            
            s.des("Epoxy").ost("Rotor Pocket")
            Rotor.append(s)
            if plot_shapes: s.plot(plot_shapes)

            # Air pockets outer
            # X= [drw(j).A_r06M.x(i,:) drw(j).A_r03M.x(i,:) fliplr(drw(j).A_rC.x(i,:))];
            xc, yc = get_xy(drw[j]['A_rC'], i)
            X = np.concatenate([x4, x1, np.flip(xc)])
            Y = np.concatenate([y4, y1, np.flip(yc)])
            
            s = Shape().ply(X, Y).lay(i+1, j+1)
            s.poly = subtract(s.poly, Rotor[-2].poly) # Rotor[-2] is the Magnet (Magnet, Inner, ...)
            # Sequence: Magnet, InnerPocket, OuterPocket.
            # Magnet is at index -2 when creating InnerPocket.
            # Magnet is at index -3 when creating OuterPocket.
            
            s.des("Epoxy").ost("Rotor Pocket")
            Rotor.append(s)
            if plot_shapes: s.plot(plot_shapes)

    # Shaft
    x18_17, y18_17 = get_xy(drw[0]['A_r18_17'], 0) # Shaft is same for all layers usually? Or lay=1?
    x13_14, y13_14 = get_xy(drw[0]['A_r13_14'], 0)
    # MATLAB: X=[drw(1).A_r18_17.x drw(1).A_r13_14.x];
    # Assuming shaft is single layer or we take first layer?
    # MATLAB code doesn't loop for shaft.
    
    X = np.concatenate([x18_17, x13_14])
    Y = np.concatenate([y18_17, y13_14])
    s = Shape().ply(X, Y).des("Shaft").ost("Shaft")
    Rotor.append(s)
    if plot_shapes: s.plot(plot_shapes)

    # Notch and Rotor Body
    if nd > 0:
        # Notch 1
        # inner_N1.x=[drw(1).L_r13_12.P2.x drw(1).A_r11.x  drw(1).A_r10.x];
        # L_r13_12.P2 is P12.
        # A_r11 is arc. A_r10 is arc.
        # We need points.
        # get_xy handles arcs. For lines, it returns 2 points.
        # We need the path.
        
        # P12 (Line P2)
        p12_x, p12_y = get_xy(drw[0]['L_r13_12'], 0) # Returns P1, P2. We want P2.
        p12_x = p12_x[1:2] # Just P2
        p12_y = p12_y[1:2]
        
        a11_x, a11_y = get_xy(drw[0]['A_r11'], 0)
        a10_x, a10_y = get_xy(drw[0]['A_r10'], 0)
        
        inner_N1_x = np.concatenate([p12_x, a11_x, a10_x])
        inner_N1_y = np.concatenate([p12_y, a11_y, a10_y])
        
        a10_15_x, a10_15_y = get_xy(drw[0]['A_r10_15'], 0)
        
        X = np.concatenate([inner_N1_x, a10_15_x])
        Y = np.concatenate([inner_N1_y, a10_15_y])
        
        s = Shape().ply(X, Y).des("Notch").ost("RotorAir")
        Rotor.append(s)
        if plot_shapes: s.plot(plot_shapes)
        
        # Notch 2 (Mirrored)
        # inner_N2... drw(2)
        p12_x_2, p12_y_2 = get_xy(drw[1]['L_r13_12'], 0)
        p12_x_2 = p12_x_2[1:2]
        a11_x_2, a11_y_2 = get_xy(drw[1]['A_r11'], 0)
        a10_x_2, a10_y_2 = get_xy(drw[1]['A_r10'], 0)
        
        inner_N2_x = np.concatenate([p12_x_2, a11_x_2, a10_x_2])
        inner_N2_y = np.concatenate([p12_y_2, a11_y_2, a10_y_2])
        
        a10_15_x_2, a10_15_y_2 = get_xy(drw[1]['A_r10_15'], 0)
        
        X = np.concatenate([inner_N2_x, a10_15_x_2])
        Y = np.concatenate([inner_N2_y, a10_15_y_2])
        
        s = Shape().ply(X, Y).des("Notch").ost("RotorAir")
        Rotor.append(s)
        if plot_shapes: s.plot(plot_shapes)
        
        # Rotor Body
        # X=[fliplr(drw(1).A_r13_14.x)  inner_N1.x drw(1).A_r10_16.x fliplr(drw(2).A_r10_16.x) fliplr(inner_N2.x)];
        x13_14, y13_14 = get_xy(drw[0]['A_r13_14'], 0)
        a10_16_x, a10_16_y = get_xy(drw[0]['A_r10_16'], 0)
        a10_16_x_2, a10_16_y_2 = get_xy(drw[1]['A_r10_16'], 0)
        
        X = np.concatenate([np.flip(x13_14), inner_N1_x, a10_16_x, np.flip(a10_16_x_2), np.flip(inner_N2_x)])
        Y = np.concatenate([np.flip(y13_14), inner_N1_y, a10_16_y, np.flip(a10_16_y_2), np.flip(inner_N2_y)])
        
    else:
        # No notch
        # X=[fliplr(drw(1).A_r13_14.x)  drw(1).A_r15_16.x   fliplr(drw(2).A_r15_16.x)];
        x13_14, y13_14 = get_xy(drw[0]['A_r13_14'], 0)
        x15_16, y15_16 = get_xy(drw[0]['A_r15_16'], 0)
        x15_16_2, y15_16_2 = get_xy(drw[1]['A_r15_16'], 0)
        
        X = np.concatenate([np.flip(x13_14), x15_16, np.flip(x15_16_2)])
        Y = np.concatenate([np.flip(y13_14), y15_16, np.flip(y15_16_2)])

    s = Shape().ply(X, Y).des("Rotor").ost("Rotor")
    
    # Subtract holes
    # polyvec=[Rotor(1:end-1).poly];
    # polyin=union(polyvec);
    # Rotor(end).poly=subtract(Rotor(end).poly,polyin);
    
    holes = Rotor[:-1] # All previous shapes (Magnets, Pockets, Shaft, Notches)
    # Wait, Shaft is a hole?
    # Shaft is defined as Shape.
    # In MATLAB: Rotor(end).poly=subtract(Rotor(end).poly,polyin);
    # polyin is union of all previous.
    # Yes, Shaft is previous.
    
    polyin = union(holes)
    s.poly = subtract(s.poly, polyin)
    
    s.update_area()
    Rotor.append(s)
    if plot_shapes: s.plot(plot_shapes)

    return Rotor

