"""Kim 2026 Fig.8-style reproduction on the SC model (16k rpm, 920 A,
beta=36 deg): FEA J(x,y) in the hottest conductor vs the analytical
superposition (Kim skin eqs 6-8 + 1-D slab proximity response behind
eq 13, Dowell direction mapping), at the same time instant.

Input : multi-step FEA txt kept by extract_sc_b.py
        (Solution blocks with ElementsTable TriIndex,Node1-3,RegCode,
         Bx,By,A,J,Je + NodesTable + RegionsTable)
Output: fig8_sc_reproduction.png + printed loss cross-check.

Conventions: phasor X with x(t)=Re[X e^{jm theta_k}], theta_k=2 pi k/N
(numpy rfft: X_m = (2/N) rfft[m]).  Prox slab response:
  B_rad (local Y): dEz/dx = +j w B  ->  J(x) = +(B/mu0) a sinh(ax)/cosh(a w/2)
  B_tan (local X): dEz/dy = -j w B  ->  J(y) = -(B/mu0) a sinh(ay)/cosh(a h/2)
with a = (1+j)/delta (low-f limits +j w s B x / -j w s B y).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.tri as mtri    # noqa: E402
import numpy as np               # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from kim_acloss import MU0, solve_ml  # noqa: E402

TXT = Path(r'C:\Users\user\AppData\Local\Temp\claude'
           r'\d--KangDH-EveryMotor'
           r'\6ca5d576-7208-4b98-afe7-21a673b592de\scratchpad'
           r'\sc_fea_txt\FullFEA_Speed_16000RPM_920.0A_36.0deg.txt')

W_C, H_C = 7.422e-3, 3.372e-3          # SC conductor [m]
SIGMA = 1.0 / 1.724e-8
F_E = 16000 * 4 / 60.0                 # electrical fundamental [Hz]
COPPER_RE = re.compile(r'^(Turn_\d+_\d+|ArmatureSlot[A-F]\d)$')
N_HARM = 8                             # analytic prox harmonics


def parse_multistep(path):
    """Stream-parse: first block topology + per-step copper J/Je/Bx/By."""
    n_steps = 0
    elems = {}          # tri -> (n1, n2, n3, regcode)   (first block)
    nodes = {}          # idx -> (x_mm, y_mm)
    regname = {}        # regcode -> name
    data = {}           # tri -> list of (Bx, By, J, Je) per step
    section = None
    first_block = True
    with open(path, encoding='latin-1') as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            if 'Solution' in s and 'Rotate' in s:
                n_steps += 1
                first_block = n_steps == 1
                section = None
                if n_steps == 2:
                    # block 1 done: keep field storage for copper
                    # elements only (full mesh x 128 steps won't fit)
                    copper = {rc for rc, nm in regname.items()
                              if COPPER_RE.match(nm)}
                    data = {i: v for i, v in data.items()
                            if elems[i][3] in copper}
                continue
            if 'ElementsTable' in s:
                section, skip = 'elem', 3
                continue
            if 'NodesTable' in s:
                section, skip = 'node', 3
                continue
            if 'RegionsTable' in s:
                section, skip = 'reg', 3
                continue
            if section is None:
                continue
            if skip > 0:
                skip -= 1
                continue
            p = s.split(',')
            try:
                if section == 'elem':
                    tri = int(p[0])
                    if first_block:
                        rc = int(p[4])
                        elems[tri] = (int(p[1]), int(p[2]), int(p[3]), rc)
                        data[tri] = []
                    row = data.get(tri)
                    if row is not None:
                        row.append((float(p[5]), float(p[6]),
                                    float(p[8]), float(p[9])))
                elif section == 'node' and first_block:
                    nodes[int(p[0])] = (float(p[1]), float(p[2]))
                elif section == 'reg' and first_block:
                    regname[int(p[0])] = p[-1].strip()
            except (ValueError, IndexError):
                section = None      # table ended (stray footer line)
    return n_steps, elems, nodes, regname, data


def load_parsed(txt_path):
    """Parse with an npz cache (the 380 MB txt takes minutes)."""
    cache = txt_path.with_suffix('.copper.npz')
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        return (int(z['n_steps']), z['elems'].item(), z['nodes'].item(),
                z['regname'].item(), z['data'].item())
    n_steps, elems, nodes, regname, data = parse_multistep(txt_path)
    np.savez_compressed(cache, n_steps=n_steps, elems=np.array(elems,
                        dtype=object), nodes=np.array(nodes, dtype=object),
                        regname=np.array(regname, dtype=object),
                        data=np.array(data, dtype=object))
    return n_steps, elems, nodes, regname, data


def main():
    print('parsing:', TXT)
    n_steps, elems, nodes, regname, data = load_parsed(TXT)
    print(f'steps={n_steps}, elements={len(elems)}, regions={len(regname)}')
    if n_steps < 8:
        raise SystemExit('multi-step export required (got '
                         f'{n_steps} steps) — rerun extract_sc_b.py')

    copper_rc = {rc for rc, nm in regname.items() if COPPER_RE.match(nm)}
    print(f'copper regions: {len(copper_rc)}')

    # element geometry
    xy = {i: np.array([nodes[n1], nodes[n2], nodes[n3]])
          for i, (n1, n2, n3, _) in elems.items()}
    area = {i: 0.5 * abs((v[1][0] - v[0][0]) * (v[2][1] - v[0][1])
                         - (v[1][1] - v[0][1]) * (v[2][0] - v[0][0]))
            for i, v in xy.items()}                       # [mm^2]

    # pick the hottest copper region by cycle-mean total-J^2 * area
    by_reg = {}
    for i, (_, _, _, rc) in elems.items():
        if rc in copper_rc and len(data[i]) == n_steps:
            by_reg.setdefault(rc, []).append(i)
    hot, hot_val = None, -1.0
    for rc, ids in by_reg.items():
        v = sum(area[i] * np.mean((np.array(data[i])[:, 2]
                                   + np.array(data[i])[:, 3])**2)
                for i in ids)
        if v > hot_val:
            hot, hot_val = rc, v
    ids = by_reg[hot]
    print(f'hottest region: {regname[hot]} ({len(ids)} elements)')

    # local frame: X = tangential (width), Y = radial (height)
    cen = np.array([xy[i].mean(axis=0) for i in ids])
    a_w = np.array([area[i] for i in ids])
    c0 = (cen * a_w[:, None]).sum(axis=0) / a_w.sum()
    th = np.arctan2(c0[1], c0[0])
    e_r = np.array([np.cos(th), np.sin(th)])
    e_t = np.array([-np.sin(th), np.cos(th)])
    lx = (cen - c0) @ e_t                                  # [mm]
    ly = (cen - c0) @ e_r

    arr = np.array([data[i] for i in ids])                 # (E, N, 4)
    bx, by, j_src, j_ed = (arr[:, :, k] for k in range(4))
    j_tot = (j_src + j_ed) * 1e-6                          # [A/mm^2]
    b_rad = np.cos(th) * bx + np.sin(th) * by
    b_tan = -np.sin(th) * bx + np.cos(th) * by

    # conductor current time series and fundamental phasor
    i_t = (j_src * (a_w[:, None] * 1e-6)).sum(axis=0)      # [A]
    ph_i = 2.0 * np.fft.rfft(i_t)[1] / n_steps
    print(f'I fundamental: {abs(ph_i):.1f} A pk (expect ~1301), '
          f'angle {np.degrees(np.angle(ph_i)):.1f} deg')

    # time step of max |I|
    k_star = int(np.argmax(np.abs(i_t)))
    th_k = 2 * np.pi * k_star / n_steps
    print(f'snapshot step {k_star}/{n_steps} (|I|={abs(i_t[k_star]):.0f} A)')

    # ---- analytical phasor fields per harmonic (local coords, meters)
    xm, ym = lx * 1e-3, ly * 1e-3
    j_hat = np.zeros((N_HARM + 1, len(ids)), dtype=complex)  # [A/m^2]

    # skin (fundamental, includes transport)
    m1, l1 = solve_ml(F_E, W_C, H_C, SIGMA)
    c_const = (ph_i / (4.0 * SIGMA)) * (m1 * l1 /
                                        (np.sinh(m1 * W_C / 2)
                                         * np.sinh(l1 * H_C / 2)))
    j_hat[1] = SIGMA * c_const * np.cosh(m1 * xm) * np.cosh(l1 * ym)

    # prox harmonics: the TS element B is the INTERNAL (shielded) field;
    # recover the applied field by dividing out the slab shielding
    # factor <B_int>/B_app = tanh(z)/z, z = alpha*u/2, before applying
    # the slab response J = +-(B_app/mu0) a sinh(a xi)/cosh(a u/2)
    wgt = a_w / a_w.sum()
    for m in range(1, N_HARM + 1):
        br = 2.0 * (wgt @ np.fft.rfft(b_rad, axis=1)[:, m]) / n_steps
        bt = 2.0 * (wgt @ np.fft.rfft(b_tan, axis=1)[:, m]) / n_steps
        delta = 1.0 / np.sqrt(np.pi * MU0 * SIGMA * m * F_E)
        al = (1 + 1j) / delta
        z_r, z_t = al * W_C / 2, al * H_C / 2
        br_app = br / (np.tanh(z_r) / z_r)
        bt_app = bt / (np.tanh(z_t) / z_t)
        j_hat[m] += ((br_app / MU0) * al * np.sinh(al * xm)
                     / np.cosh(al * W_C / 2)
                     - (bt_app / MU0) * al * np.sinh(al * ym)
                     / np.cosh(al * H_C / 2))

    steps_m = np.exp(1j * np.arange(N_HARM + 1)[:, None] * th_k)
    j_ana_t = np.real(j_hat * steps_m).sum(axis=0) * 1e-6   # [A/mm^2]
    j_ana_rms = np.sqrt(0.5 * (np.abs(j_hat)**2).sum(axis=0)) * 1e-6
    j_fea_rms = np.sqrt((j_tot**2).mean(axis=1))

    # ---- loss cross-check (cycle mean, this conductor, active length)
    l_act = 0.150
    p_fea = l_act * ((j_tot * 1e6)**2 *
                     (a_w[:, None] * 1e-6)).sum(axis=0).mean() / SIGMA
    p_ana = l_act * ((j_ana_rms * 1e6)**2 * (a_w * 1e-6)).sum() / SIGMA
    r_dc = l_act / (SIGMA * W_C * H_C)
    print(f'FEA cycle-mean loss (this bar): {p_fea:.1f} W | '
          f'analytical {p_ana:.1f} W | DC {0.5 * abs(ph_i)**2 * r_dc:.1f} W')
    top = np.argsort(-j_fea_rms)[:3]
    for t in top:
        print(f'  FEA-RMS hotspot: elem {ids[t]} at local '
              f'({lx[t]:+.2f}, {ly[t]:+.2f}) mm, '
              f'Jrms {j_fea_rms[t]:.1f} A/mm2')

    # ---- figure
    tris = []
    node_ids, node_xy = {}, []
    for i in ids:
        vv = []
        for n in elems[i][:3]:
            if n not in node_ids:
                node_ids[n] = len(node_xy)
                p = np.array(nodes[n]) - c0
                node_xy.append([p @ e_t, p @ e_r])
            vv.append(node_ids[n])
        tris.append(vv)
    node_xy = np.array(node_xy)
    tri_obj = mtri.Triangulation(node_xy[:, 0], node_xy[:, 1],
                                 np.array(tris))

    j_fea_k = j_tot[:, k_star]
    vmax = max(np.abs(j_fea_k).max(), np.abs(j_ana_t).max())
    # clip the corner-singularity outlier so the shared scale stays useful
    rmax = np.percentile(np.concatenate([j_fea_rms, j_ana_rms]), 99)
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.6),
                             sharex=True, sharey=True)
    panels = [
        (axes[0, 0], j_fea_k, f'TS-FEA  J(x,y)  @ step {k_star} (|I| max)',
         'RdBu_r', -vmax, vmax),
        (axes[0, 1], j_ana_t, 'Analytical, same instant',
         'RdBu_r', -vmax, vmax),
        (axes[1, 0], j_fea_rms, 'TS-FEA  cycle-RMS |J|',
         'inferno', 0, rmax),
        (axes[1, 1], j_ana_rms, 'Analytical  cycle-RMS |J|',
         'inferno', 0, rmax),
    ]
    for ax, vals, ttl, cm, v0, v1 in panels:
        pc = ax.tripcolor(tri_obj, facecolors=vals, cmap=cm,
                          vmin=v0, vmax=v1)
        ax.set_aspect('equal')
        ax.set_title(ttl, fontsize=9.5)
        cb = fig.colorbar(pc, ax=ax, fraction=0.046, pad=0.03)
        cb.set_label('J [A/mm$^2$]', fontsize=8)
        cb.ax.tick_params(labelsize=7)
    for ax in axes[1]:
        ax.set_xlabel('tangential x [mm]', fontsize=9)
    for ax in axes[:, 0]:
        ax.set_ylabel('radial y [mm]', fontsize=9)
    fig.suptitle(f'SC 16k rpm, 920 A, 36°  —  conductor {regname[hot]}  '
                 f'(analytical = Kim skin + 1-D slab prox, applied-field '
                 f'corrected)', fontsize=10)
    fig.tight_layout()
    out = HERE / 'fig8_sc_reproduction.png'
    fig.savefig(out, dpi=200, bbox_inches='tight')
    print('saved:', out)


if __name__ == '__main__':
    main()
