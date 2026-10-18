"""Resolved e10 manual-hairpin sampling; geometry in mm, returned points in m.

This bounded adapter reproduces the validated Ref geometry. It is not the
Motor-CAD geometry engine. Scaling all lengths preserves the Ref-only method.
The loss dimensions remain bare copper; sampling includes insulation.
"""
import math
import numpy as np
from .hybrid_kernel import polynomial_band_weights, rectangular_proximity_coefficient, native_rectangular_skin_loss


def sampling_geometry(settings):
    n = int(settings['NumberOfCuboids'])
    if n != 6:
        raise ValueError('Only the validated e10 six-cuboid layout is supported')
    total = int(settings['HybridModel_TotalLines'])
    power = settings['HybridModel_PolynomialPower']
    heights = np.array([settings[f'Winding_Cuboid_Height[{i}]'] for i in range(n)])
    height = heights.sum()
    q = math.ceil(total * 1.1)
    t = q - total
    edges = height * (np.arange(t, q+1, dtype=float)**power-t**power)/(q**power-t**power)
    mids = (edges[:-1]+edges[1:])/2
    width = settings['Copper_Width'] + 2*settings['Insulation_Thickness']
    copper_height = settings['Copper_Height'] + 2*settings['Insulation_Thickness']
    used = 0
    points, weights, cuboids, sides, counts = [], [], [], [], []
    for c in range(n):
        high = height-heights[:c].sum()
        low = high-heights[c]
        count = max(1, int(np.sum((mids[:total-used] < high) & (mids[:total-used] > low))))
        counts.append(count)
        bands = np.array(polynomial_band_weights(total, used, count, power))
        extent = copper_height if c == n-1 else heights[c]
        cx = settings[f'ConductorCentre_L_x[0][{c}]']
        cy = settings[f'ConductorCentre_L_y[0][{c}]']
        y = cy+copper_height/2-extent*(np.cumsum(bands)-bands/2)
        for side in (0, 1):
            xa, xb = (cx-width/2, 0) if side == 0 else (0, cx+width/2)
            for line, yy in enumerate(y):
                for j in range(1, 11):
                    points.append([xa+(xb-xa)*j/11, yy])
                    weights.append(bands[line]/10)
                    cuboids.append(c)
                    sides.append(side)
        used += count
    theta = np.deg2rad(-90-360/48/2)
    rotation = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    return dict(points_m=np.asarray(points)@rotation.T/1000,
                weight=np.asarray(weights), cuboid=np.asarray(cuboids),
                side=np.asarray(sides), line_counts=counts)


def evaluate_active_samples(b_magnitude_T, geometry, contract, current_Arms, rpm, radial_factor=1.):
    """Evaluate raw phase-by-point B magnitudes without FFT or loss-label fitting.

    B must come from the matching Ref current/phase (not scaled by current here).
    The frequency-independent MS field transfers with exact radial similarity.
    Active skin uses each actual Elmer bar area and its prescribed RMS current.
    """
    b = np.asarray(b_magnitude_T, dtype=float)
    if b.ndim != 2 or b.shape[1] != len(geometry['weight']) or not np.isfinite(b).all():
        raise ValueError('Expected finite [phase, sample] scalar B history')
    if current_Arms < 0 or min(rpm, radial_factor) <= 0 or (b < 0).any():
        raise ValueError('Nonnegative current/B and positive speed/scale required')
    if not np.isclose(current_Arms/radial_factor, contract['Ref_current_Arms'], rtol=1e-12):
        raise ValueError('This Ref field is available only for matching current similarity')
    s = contract['geometry_settings_mm']
    rho = 1/contract['sigma_S_m']
    length = contract['active_length_m']
    width = s['Copper_Width']*radial_factor/1000
    height = s['Copper_Height']*radial_factor/1000
    freq = rpm*contract['pole_pairs']/60
    coefficient = rectangular_proximity_coefficient(length, width, height, freq, rho, 1)
    valid = np.asarray(geometry.get('valid', np.ones(b.shape[1], dtype=bool)), dtype=bool)
    wave = np.zeros(b.shape[0])
    for c in range(6):
        for side in (0, 1):
            mask = (geometry['cuboid'] == c) & (geometry['side'] == side) & valid
            w = geometry['weight'][mask]
            if not len(w) or w.sum() <= 0:
                raise ValueError('Cuboid side has no valid sampled area')
            # g=1/6 and Ncond=6; native 1/2 allocates the two sides.
            wave += coefficient*contract['slots']/2*((b[:, mask]**2)@w)/w.sum()
    areas = np.asarray(list(contract['Ref_bar_areas_m2'].values()))*radial_factor**2
    if len(areas) != 36 or np.any(areas <= 0):
        raise ValueError('Expected 36 positive bar areas in the 1/8 sector')
    skin = contract['symmetry']*sum(native_rectangular_skin_loss(
        current_Arms/(area*1e6), freq, width, height, rho, area*length) for area in areas)
    proximity = float(wave.mean())
    return dict(hybrid_W=proximity+skin, hybrid_proximity_W=proximity,
                hybrid_skin_excess_W=skin, proximity_waveform_W=wave,
                frequency_Hz=freq, coefficient_W_T2=coefficient,
                active_volume_m3=float(contract['symmetry']*length*areas.sum()),
                mean_spatial_B2_weighted_T2=proximity/coefficient/(48*6))
