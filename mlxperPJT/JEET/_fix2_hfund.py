"""
FIX-2: _h_fund auto-detect patch
Replaces hardcoded nh==1 / omega_n=nh*omega with dynamic _h_fund/_omega_per_h.
Also adds node-match diagnostic to A5b.
"""
import json, sys, pathlib
sys.stdout.reconfigure(encoding='utf-8')

NB_PATH = pathlib.Path(r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\pyMorisco_FFT_PEEC_Method34.ipynb")

with open(NB_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']
id_to_idx = {c.get('id'): i for i, c in enumerate(cells)}

def get_src(cell_id):
    c = cells[id_to_idx[cell_id]]
    s = c['source']
    return s if isinstance(s, str) else ''.join(s)

def set_src(cell_id, new_src):
    idx = id_to_idx[cell_id]
    c = cells[idx]
    if isinstance(c['source'], list):
        c['source'] = new_src.splitlines(keepends=True)
    else:
        c['source'] = new_src

checks = []

# ─────────────────────────────────────────────────────────────
# A5b: Add matched-elements diagnostic
# ─────────────────────────────────────────────────────────────
OLD_A5B = "print(f\"[A5b] No-load B/H: ({n_steps_nl} x {n_elem_total}), {time.perf_counter()-t0_nl:.1f}s\")"
NEW_A5B = """\
# Matched-elements diagnostic
matched_mask = np.any(np.abs(bx_nl_ts) + np.abs(by_nl_ts) > 0, axis=0)
n_matched = int(matched_mask.sum())
print(f"[A5b] No-load B/H: ({n_steps_nl} x {n_elem_total}), {time.perf_counter()-t0_nl:.1f}s")
print(f"  Node match: {n_matched}/{n_elem_total} elements ({100*n_matched/n_elem_total:.1f}%)")
if n_matched < n_elem_total * 0.5:
    print("  [WARN] <50% matched -- possible mesh mismatch between no-load and hybrid FEA!")\
"""

src_a5b = get_src('a5b_noload_bh')
if OLD_A5B in src_a5b:
    set_src('a5b_noload_bh', src_a5b.replace(OLD_A5B, NEW_A5B))
    checks.append('A5b: node-match diagnostic OK')
else:
    checks.append('A5b: OLD_A5B not found (already patched?)')

# ─────────────────────────────────────────────────────────────
# D1: Replace harmonic_indices block + E-section loop
# ─────────────────────────────────────────────────────────────
OLD_D1_SPEC = """\
# Significant harmonics
mag_spectrum = np.abs(I_mag_phasor).max(axis=1)
mag_fund = mag_spectrum[1] if n_freq > 1 else 1.0
significant_mask = mag_spectrum > (0.01 * mag_fund)
significant_mask[0] = False  # Remove DC
harmonic_indices = np.where(significant_mask)[0]
print(f"  Significant harmonics (>1% fund): {significant_mask.sum()}")
for nh in harmonic_indices[:5]:
    print(f"    n={nh}: {mag_spectrum[nh]:.1f} A ({mag_spectrum[nh]/mag_fund*100:.1f}%)")\
"""

NEW_D1_SPEC = """\
# Significant harmonics
mag_spectrum = np.abs(I_mag_phasor).max(axis=1)
# _h_fund: dominant non-DC bin = electrical fundamental
# (=1 for 1 electrical period; =POLE_PAIRS for 1 mechanical period data)
_spec_no_dc = mag_spectrum.copy(); _spec_no_dc[0] = 0.0
_h_fund = max(int(np.argmax(_spec_no_dc)), 1)
mag_fund = mag_spectrum[_h_fund]
_omega_per_h = omega / _h_fund  # angular frequency per FFT bin
significant_mask = mag_spectrum > (0.01 * mag_fund)
significant_mask[0] = False  # Remove DC
harmonic_indices = np.where(significant_mask)[0]
print(f"  [FIX-1] fund_h={_h_fund}, f_fund={_omega_per_h*_h_fund/(2*np.pi):.0f} Hz, sig={significant_mask.sum()}")
for nh in harmonic_indices[:5]:
    print(f"    n={nh}: {mag_spectrum[nh]:.1f} A ({mag_spectrum[nh]/mag_fund*100:.1f}%)")\
"""

OLD_D1_OMEGA = "    omega_n = n_h * omega\n    Z_n = R_matrix + 1j * omega_n * L_matrix"
NEW_D1_OMEGA = "    omega_n = n_h * _omega_per_h\n    Z_n = R_matrix + 1j * omega_n * L_matrix"

OLD_D1_COND = "    if n_h == 1:"
NEW_D1_COND = "    if n_h == _h_fund:"

src_d1 = get_src('73098640')
mod = src_d1
if OLD_D1_SPEC in mod:
    mod = mod.replace(OLD_D1_SPEC, NEW_D1_SPEC)
    checks.append('D1: harmonic_indices block OK')
else:
    checks.append('D1: OLD_D1_SPEC not found')

if OLD_D1_OMEGA in mod:
    mod = mod.replace(OLD_D1_OMEGA, NEW_D1_OMEGA)
    checks.append('D1: omega_n replace OK')
else:
    checks.append('D1: OLD_D1_OMEGA not found')

if OLD_D1_COND in mod:
    mod = mod.replace(OLD_D1_COND, NEW_D1_COND)
    checks.append('D1: if n_h==1 replace OK')
else:
    checks.append('D1: OLD_D1_COND not found')

set_src('73098640', mod)

# ─────────────────────────────────────────────────────────────
# D3: omega_n, if nh==1, i_harms[1], J_eddy
# ─────────────────────────────────────────────────────────────
OLD_D3_OMEGA = "        omega_n = nh * omega\n        Z_n = R_matrix + 1j * omega_n * L_matrix"
NEW_D3_OMEGA = "        omega_n = nh * _omega_per_h\n        Z_n = R_matrix + 1j * omega_n * L_matrix"

OLD_D3_COND = """\
        if nh == 1:
            i_imp_s = ZnC @ np_solve(CZnC, I_test)
            i_harms[1] = i_imp_s + i_raw + i_corr\
"""
NEW_D3_COND = """\
        if nh == _h_fund:
            i_imp_s = ZnC @ np_solve(CZnC, I_test)
            i_harms[_h_fund] = i_imp_s + i_raw + i_corr\
"""

OLD_D3_JEDDY = "    J_eddy = np.abs(i_harms[1] - i_imp_s) / grid_local.area_fil * 1e-6"
NEW_D3_JEDDY = "    J_eddy = np.abs(i_harms[_h_fund] - i_imp_s) / grid_local.area_fil * 1e-6"

src_d3 = get_src('55035f0d')
mod = src_d3
if OLD_D3_OMEGA in mod:
    mod = mod.replace(OLD_D3_OMEGA, NEW_D3_OMEGA)
    checks.append('D3: omega_n replace OK')
else:
    checks.append('D3: OLD_D3_OMEGA not found')

if OLD_D3_COND in mod:
    mod = mod.replace(OLD_D3_COND, NEW_D3_COND)
    checks.append('D3: if nh==1/i_harms[1] replace OK')
else:
    checks.append('D3: OLD_D3_COND not found')

if OLD_D3_JEDDY in mod:
    mod = mod.replace(OLD_D3_JEDDY, NEW_D3_JEDDY)
    checks.append('D3: J_eddy replace OK')
else:
    checks.append('D3: OLD_D3_JEDDY not found')

set_src('55035f0d', mod)

# ─────────────────────────────────────────────────────────────
# D5: omega_n, if nh==1 (phasors loop), if nh==1 (reconstruct)
# ─────────────────────────────────────────────────────────────
OLD_D5_OMEGA = "    omega_n = nh * omega\n    Z_n = R_matrix + 1j * omega_n * L_matrix\n    Z_n_inv = inv(Z_n); ZnC = Z_n_inv @ C; CZnC = C.T @ ZnC\n    V_n = 1j * omega_n * (L_w_int @ I_mag_fft_ext[nh])"
NEW_D5_OMEGA = "    omega_n = nh * _omega_per_h\n    Z_n = R_matrix + 1j * omega_n * L_matrix\n    Z_n_inv = inv(Z_n); ZnC = Z_n_inv @ C; CZnC = C.T @ ZnC\n    V_n = 1j * omega_n * (L_w_int @ I_mag_fft_ext[nh])"

OLD_D5_COND = """\
    if nh == 1:
        peec_imp_phasor = ZnC @ np_solve(CZnC, I_test)
        peec_phasors[nh] = peec_imp_phasor + i_raw + i_corr\
"""
NEW_D5_COND = """\
    if nh == _h_fund:
        peec_imp_phasor = ZnC @ np_solve(CZnC, I_test)
        peec_phasors[nh] = peec_imp_phasor + i_raw + i_corr\
"""

OLD_D5_RECON = "        if nh == 1:\n            i_imp += np.real(peec_imp_phasor * np.exp(1j * phase))"
NEW_D5_RECON = "        if nh == _h_fund:\n            i_imp += np.real(peec_imp_phasor * np.exp(1j * phase))"

src_d5 = get_src('b7b29b01')
mod = src_d5
if OLD_D5_OMEGA in mod:
    mod = mod.replace(OLD_D5_OMEGA, NEW_D5_OMEGA)
    checks.append('D5: omega_n replace OK')
else:
    checks.append('D5: OLD_D5_OMEGA not found')

if OLD_D5_COND in mod:
    mod = mod.replace(OLD_D5_COND, NEW_D5_COND)
    checks.append('D5: if nh==1 phasors replace OK')
else:
    checks.append('D5: OLD_D5_COND not found')

if OLD_D5_RECON in mod:
    mod = mod.replace(OLD_D5_RECON, NEW_D5_RECON)
    checks.append('D5: if nh==1 reconstruct replace OK')
else:
    checks.append('D5: OLD_D5_RECON not found')

set_src('b7b29b01', mod)

# ─────────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────────
with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("=== FIX-2 Patch Results ===")
for c in checks:
    status = "OK" if "not found" not in c else "MISSING"
    print(f"  [{status}] {c}")

total_ok = sum(1 for c in checks if "not found" not in c)
total = len(checks)
print(f"\n{total_ok}/{total} checks passed")
