"""Element-level mesh-B replication of the Hybrid AC-loss methods vs the
Motor-CAD internal Hybrid values, at exact sweep grid points.

Usage:  python mesh_b_vs_mcad.py [halfsc|sc]

Methods compared (proximity, machine level):
  P24 solid   : /24 low-frequency kernel, solid-conductor dims
  P24 cuboid6 : /24 with the radial-field eddy path limited to the
                cuboid width w/6 (emulates the Volpe/Motor-CAD cuboidal
                subdivision; suppresses that term by 6^2)
  G2 solid    : full transcendental kernel g (paper eq (3)),
                direction-split, area-weighted <B_m^2> per element,
                isotropic skin depth delta = sqrt(2/(omega*mu*sigma))
  Volpe G2p   : same transcendental kernel but with anisotropic modified
                skin depth (calcSkinDepthModi.m port):
                  delta_w = delta * sqrt((w+h)/(2h))  [along width]
                  delta_h = delta * sqrt((h+w)/(2w))  [along height]
                This is the "prime" variant (calcProx2DG2Prime.m) that
                Motor-CAD uses internally.  Accounts for conductor aspect
                ratio; identical to G2 solid for square cross-sections.
  Kim (KDE)   : reactance-limited kernel (Kim 2026 eq (13)) fed with the
                KDE-representative element field amplitudes (eqs 14-15),
                sinusoidal part only (no PWM)
plus the Kim reactance-limited skin (eqs 5-9) vs the MCAD skin column.

Conventions: FFT one-sided PEAK amplitudes; radial/tangential split by
rotating the element time series at the slot centroid angle (exact);
machine total = 8 sectors x 36 conductor regions.

B-source caveat: the HalfSC b_dir holds MS-swept fields (Hybrid
export); the SC b_dir is extracted from the archived FullFEA TS .mes
(no MS export survived the *_no_txt cleanup), so the SC element B
includes conductor eddy reaction — a slight underestimate of the
source field at 16k rpm.  The TS solve also starts from the
magnetostatic state (step-1 B matches a live MS solve to 0.2%), so
the first ~tau/T of the exported cycle carries the eddy start-up
transient (tau ~ 0.2 ms: ~3% of the cycle at 2k rpm, ~20% at 16k) —
the one-cycle FFT amplitudes at 16k inherit a small bias from it.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

try:  # imported as the package ``acloss_ref_methods``
    from .kim_acloss import (kde_representative, prox_loss_kim,
                             skin_loss_kim)
    from .volpe_hybrid_acloss import (calc_prox_2D_G2 as _volpe_prox_g2p,
                                      calc_skin_loss,
                                      SIGMA_CU_20C as _SIGMA_V,
                                      MU_0 as _MU_V)
except ImportError:  # run from inside acloss_ref_methods/ (legacy)
    from kim_acloss import (kde_representative, prox_loss_kim,
                            skin_loss_kim)
    from volpe_hybrid_acloss import (calc_prox_2D_G2 as _volpe_prox_g2p,
                                     calc_skin_loss,
                                     SIGMA_CU_20C as _SIGMA_V,
                                     MU_0 as _MU_V)

HERE = Path(__file__).resolve().parent


def _map_e10() -> Path:
    """Reduced data root: ``JEET_DATA_ROOT`` > repro_env > sibling map_exports."""
    env = os.environ.get('JEET_DATA_ROOT')
    if env:
        return Path(env)
    try:
        from jeet_acloss_rbf.repro_env import data_root
        return Path(data_root())
    except ImportError:
        return HERE.parent / 'map_exports' / 'e10'


MAP_E10 = _map_e10()

MODELS = {
    'halfsc': dict(
        w=5.5665e-3, h=2.529e-3,
        b_dir=HERE / 'elhajji_b_data',
        mcad_json=MAP_E10 / 'HalfSC' / 'JEET_ACLoss_HalfSC_Map_Summary.json',
        cases=[(2000, '460.0', 36.0), (2000, '460.0', 54.0),
               (4000, '460.0', 36.0), (4000, '460.0', 54.0),
               (8000, '460.0', 18.0), (8000, '460.0', 54.0),
               (16000, '460.0', 36.0), (16000, '460.0', 54.0)],
    ),
    'sc': dict(
        # B source: FullFEA TS .mes (archived); conductor eddy reaction
        # included — P24/G2/Volpe computed with TS B (overestimates Hybrid
        # replication).  Use 'sc_hybrid' once extract_sc_b_hybrid.py runs.
        w=7.422e-3, h=3.372e-3,
        b_dir=HERE / 'sc_b_data',
        mcad_json=MAP_E10 / 'SC' / 'JEET_ACLoss_SC_Map_Summary.json',
        cases=[(2000, '920.0', 36.0), (4000, '920.0', 36.0),
               (8000, '920.0', 36.0), (16000, '920.0', 36.0),
               (16000, '920.0', 54.0), (16000, '460.1', 36.0)],
    ),
    'sc_hybrid': dict(
        # B source: Motor-CAD Hybrid_Speed_* MS .mes (sigma=0 conductors) —
        # faithful source field for Hybrid /24 replication.
        # Run extract_sc_b_hybrid.py on Windows first to populate sc_b_data_hybrid/.
        w=7.422e-3, h=3.372e-3,
        b_dir=HERE / 'sc_b_data_hybrid',
        mcad_json=MAP_E10 / 'SC' / 'JEET_ACLoss_SC_Map_Summary.json',
        cases=[(2000, '920.0', 36.0), (4000, '920.0', 36.0),
               (8000, '920.0', 36.0), (16000, '920.0', 36.0),
               (16000, '920.0', 54.0), (16000, '460.1', 36.0)],
    ),
}

L_ACTIVE = 0.150
SIGMA = 1.0 / 1.724e-8
MU0 = 4e-7 * np.pi
POLE_PAIRS = 4
SECTORS = 8
N_COND = 48 * 6


def kernel(eta: np.ndarray) -> np.ndarray:
    return (np.sinh(eta) - np.sin(eta)) / (np.cosh(eta) + np.cos(eta))


def prox_g2(f, b2_tan, b2_rad, w, h) -> float:
    """Full-kernel prox per conductor [W] (Dowell direction mapping, isotropic delta)."""
    delta = 1.0 / np.sqrt(np.pi * f * MU0 * SIGMA)
    g_t = (w / delta) / (SIGMA * MU0**2) * kernel(h / delta)
    g_r = (h / delta) / (SIGMA * MU0**2) * kernel(w / delta)
    return float(np.sum(g_t * b2_tan + g_r * b2_rad) * L_ACTIVE)


def prox_g2_volpe_prime(f, b2_tan, b2_rad, w, h) -> float:
    """Volpe G2 prime: full kernel with anisotropic modified skin depth [W].

    Uses calc_prox_2D_G2(use_modified_delta=True) from volpe_hybrid_acloss,
    which ports calcProx2DG2Prime.m / calcSkinDepthModi.m.

    Direction mapping (matches Dowell convention used in prox_g2):
      b_tan (along conductor width w)  -> Br  (paired with gw * kernel(gh))
      b_rad (along conductor height h) -> Btheta (paired with gh * kernel(gw))

    b2_tan / b2_rad are area-weighted mean B^2 [T^2] per harmonic;
    sqrt converts to RMS-equivalent peak B before squaring inside calc_prox_2D_G2.
    """
    return float(np.sum(
        _volpe_prox_g2p(w, h, f, L_ACTIVE,
                        np.sqrt(b2_tan), np.sqrt(b2_rad),
                        _SIGMA_V, _MU_V,
                        use_modified_delta=True)))


def prox_24(f, b2_tan, b2_rad, w, h, n_cuboids: int = 1) -> float:
    """Low-frequency /24 prox per conductor [W]."""
    w2 = (2 * np.pi * f) ** 2
    p_t = SIGMA * w * h**3 * L_ACTIVE * w2 * b2_tan / 24.0
    p_r = (SIGMA * h * w**3 * L_ACTIVE * w2 * b2_rad / 24.0
           / (n_cuboids ** 2))
    return float(np.sum(p_t + p_r))


def mcad_reference(path: Path, current: float) -> dict:
    db = json.load(open(path, encoding='utf-8'))
    recs = db.get('records', db) if isinstance(db, dict) else db
    out = {}
    for r in recs:
        if abs(r.get('current', 0) - current) > 1:
            continue
        key = (int(r['speed']), round(float(r['phase']), 1))
        e = out.setdefault(key, {})
        if r.get('mode') == 'Hybrid':
            e['prox_W'] = r.get('hybrid_prox_kW', 0) * 1e3
            e['skin_W'] = r.get('hybrid_skin_kW', 0) * 1e3
        elif r.get('mode') == 'FullFEA':
            v = r.get('ts_ac_active_only_kW')
            e['ts_W'] = v * 1e3 if v is not None else None
    return out


def main() -> None:
    model = (sys.argv[1] if len(sys.argv) > 1 else 'halfsc').lower()
    cfg = MODELS[model]
    w_c, h_c = cfg['w'], cfg['h']
    print(f'=== model {model}: conductor {w_c*1e3:.3f} x {h_c*1e3:.3f} mm, '
          f'L={L_ACTIVE*1e3:.0f} mm ===')

    print(f"{'case':>16s} {'P24sol':>9s} {'P24cub6':>9s} {'G2sol':>9s} "
          f"{'VlpG2p':>9s} {'KimKDE':>9s} {'MCADpx':>9s} {'TS':>9s} "
          f"{'cub/M':>6s} {'G2/TS':>6s} {'Vlp/M':>6s} {'Vlp/TS':>7s} {'Kim/M':>6s}")
    rows = []
    for spd, cur, ph in cfg['cases']:
        p = cfg['b_dir'] / f'Hybrid_Speed_{spd}RPM_{cur}A_{ph}deg.json'
        if not p.exists():
            print(f'{spd:>7d}/{cur}/{ph:<4.0f} missing: {p.name}')
            continue
        d = json.load(open(p, encoding='utf-8'))
        f_e = spd * POLE_PAIRS / 60.0
        n_steps = d['n_steps_total']
        f_m = np.arange(1, n_steps // 2 + 1) * f_e

        p24 = p24c = g2 = volpe = kim = 0.0
        for reg in d['regions']:
            wgt = np.array([e['w_mm2'] for e in reg['elements']])
            bx = np.array([e['Bx_T'] for e in reg['elements']])
            by = np.array([e['By_T'] for e in reg['elements']])
            x, y = reg['centroid_xy_mm']
            th = np.arctan2(y, x)
            b_rad = np.cos(th) * bx + np.sin(th) * by
            b_tan = -np.sin(th) * bx + np.cos(th) * by

            n = bx.shape[1]
            amp_r = 2.0 * np.abs(np.fft.rfft(b_rad, axis=1))[:, 1:] / n
            amp_t = 2.0 * np.abs(np.fft.rfft(b_tan, axis=1))[:, 1:] / n
            wn = wgt / wgt.sum()
            b2_rad = wn @ amp_r**2
            b2_tan = wn @ amp_t**2

            p24 += prox_24(f_m, b2_tan, b2_rad, w_c, h_c)
            p24c += prox_24(f_m, b2_tan, b2_rad, w_c, h_c, n_cuboids=6)
            g2 += prox_g2(f_m, b2_tan, b2_rad, w_c, h_c)
            volpe += prox_g2_volpe_prime(f_m, b2_tan, b2_rad, w_c, h_c)

            rep_r = np.array([kde_representative(amp_r[:, m])
                              for m in range(amp_r.shape[1])])
            rep_t = np.array([kde_representative(amp_t[:, m])
                              for m in range(amp_t.shape[1])])
            # dowell_mapping: the as-printed (u_i, u_j) of eq (13) gives
            # 2.3x at low speed; the Dowell mapping reproduces TS-FEA
            # within +-15% at all speeds (kim_mapping_check.py)
            kim += prox_loss_kim(rep_r, rep_t, f_m, w_c, h_c,
                                 L_ACTIVE, SIGMA, dowell_mapping=True)
        p24 *= SECTORS
        p24c *= SECTORS
        g2 *= SECTORS
        volpe *= SECTORS
        kim *= SECTORS

        ref = mcad_reference(cfg['mcad_json'], float(cur))
        e = ref.get((spd, ph), {})
        mp = e.get('prox_W', float('nan'))
        ts = e.get('ts_W', float('nan')) or float('nan')
        rows.append(dict(speed=spd, current=float(cur), phase=ph,
                         P24_solid_W=p24, P24_cuboid6_W=p24c,
                         G2_solid_W=g2, Volpe_G2p_W=volpe,
                         Kim_KDE_W=kim,
                         mcad_prox_W=mp, ts_ac_W=ts,
                         Volpe_over_MCAD=volpe/mp if mp else None,
                         Volpe_over_TS=volpe/ts if ts and not np.isnan(ts) else None))
        print(f'{spd:>6d}/{cur}/{ph:<4.0f} {p24/1e3:9.2f} {p24c/1e3:9.2f} '
              f'{g2/1e3:9.2f} {volpe/1e3:9.2f} {kim/1e3:9.2f} '
              f'{mp/1e3:9.2f} {ts/1e3:9.2f} '
              f'{p24c/mp:6.2f} {g2/ts:6.2f} {volpe/mp:6.2f} {volpe/ts:7.2f} {kim/mp:6.2f}   [kW]')

    # Skin (fundamental, EXCESS) vs MCAD skin column.  Kim's corner-
    # crowding form is out of its validity domain at the fundamental
    # (see kim_acloss docstring) — reported for reference only, never
    # summed into totals; Dowell/k_s^rect is the validated choice.
    print('\nFundamental EXCESS skin vs MCAD skin [kW] '
          '(Kim: reference only):')
    seen = set()
    for spd, cur, ph in cfg['cases']:
        if (spd, cur) in seen:
            continue
        seen.add((spd, cur))
        f_e = spd * POLE_PAIRS / 60.0
        i_amp = np.sqrt(2.0) * float(cur)
        p_sk = N_COND * skin_loss_kim(i_amp, f_e, w_c, h_c,
                                      L_ACTIVE, SIGMA, excess=True)
        p_dw = N_COND * calc_skin_loss(w_c, h_c, f_e, L_ACTIVE,
                                       float(cur))['P_excess_W']
        ref = mcad_reference(cfg['mcad_json'], float(cur))
        ms = np.nanmean([v.get('skin_W', np.nan)
                         for k, v in ref.items() if k[0] == spd])
        print(f'  {spd:>6d} rpm @ {cur} A: Kim {p_sk/1e3:8.3f} | '
              f'Dowell {p_dw/1e3:8.3f} | MCAD {ms/1e3:8.3f} | '
              f'Kim/Dw {p_sk/p_dw:5.2f} Dw/MC {p_dw/ms:5.2f}')

    out = HERE / f'mesh_b_vs_mcad_{model}.json'
    json.dump(rows, open(out, 'w', encoding='utf-8'), indent=1)
    print('\nsaved:', out)


if __name__ == '__main__':
    main()
