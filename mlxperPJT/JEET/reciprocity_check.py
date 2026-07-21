# -*- coding: utf-8 -*-
"""
reciprocity_check.py  -- paper2 Phase B, task B1
================================================
e10_SatuMap.mat 자속맵의 가역성(reciprocity) 잔차를 정량화한다.

보존(conservative) 자기 공에너지 W'(i_d,i_q)가 존재하면
    λ_d = ∂W'/∂i_d,  λ_q = ∂W'/∂i_q
이므로 교차 2차미분이 같아야 한다 (Maxwell 상호성):
    ∂λ_d/∂i_q = ∂λ_q/∂i_d.
잔차  r(i_d,i_q) = ∂λ_d/∂i_q − ∂λ_q/∂i_d  [H]
가 0이 아니면 λ_d, λ_q 독립 보간이 **비보존장**이 되어, 과도 MIL에서
저장에너지 항 (3/2)(i_d dλ_d + i_q dλ_q)가 경로의존이 되고 한 사이클에서
에너지를 생성/소멸시킨다 (순시 전력수지 위반의 #1 원인).

Green 정리:  닫힌 루프 ∮(λ_d di_d + λ_q di_q)
           = ∬ (∂λ_q/∂i_d − ∂λ_d/∂i_q) di_d di_q = −∬ r di_d di_q
→ 맵 전체의 스퓨리어스 공에너지 = |∬ r di_d di_q| [J].

출력:
  map_exports/e10/paper2_phaseA/reciprocity_residual.png
  map_exports/e10/paper2_phaseA/PhaseB_reciprocity_report.md
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import loadmat

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
SAT = (HERE.parent.parent / "tools" / "SystemSimulationModel"
       / "e10_SatuMap.mat")
OUT_DIR = HERE / "map_exports" / "e10" / "paper2_phaseA"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def to_regular(idg, iqg, ld, lq):
    """산점 (id,iq,λ)를 정규 격자 [id, iq]로 재배열."""
    id_1d = np.unique(idg)
    iq_1d = np.unique(iqg)
    LD = np.full((id_1d.size, iq_1d.size), np.nan)
    LQ = np.full((id_1d.size, iq_1d.size), np.nan)
    idg_f = idg.ravel()
    iqg_f = iqg.ravel()
    ld_f = ld.ravel()
    lq_f = lq.ravel()
    for k in range(idg_f.size):
        i = np.argmin(np.abs(id_1d - idg_f[k]))
        j = np.argmin(np.abs(iq_1d - iqg_f[k]))
        LD[i, j] = ld_f[k]
        LQ[i, j] = lq_f[k]
    return id_1d, iq_1d, LD, LQ


def main() -> None:
    d = loadmat(str(SAT))
    idg = np.squeeze(d["Id_Peak"]).astype(float)
    iqg = np.squeeze(d["Iq_Peak"]).astype(float)
    ld = np.squeeze(d["Flux_Linkage_D"]).astype(float)
    lq = np.squeeze(d["Flux_Linkage_Q"]).astype(float)

    id_1d, iq_1d, LD, LQ = to_regular(idg, iqg, ld, lq)
    print(f"grid: {id_1d.size} id x {iq_1d.size} iq")
    print(f"  id_1d = {np.round(id_1d, 1)}")
    print(f"  iq_1d = {np.round(iq_1d, 1)}")

    # 교차 미분: ∂λ_d/∂i_q (axis=1),  ∂λ_q/∂i_d (axis=0)
    dLd_diq = np.gradient(LD, iq_1d, axis=1)   # H
    dLq_did = np.gradient(LQ, id_1d, axis=0)   # H
    r = dLd_diq - dLq_did                       # H (residual)

    scale = 0.5 * (np.abs(dLd_diq) + np.abs(dLq_did))
    rel = np.abs(r) / (scale + 1e-9) * 100.0    # %

    # 스퓨리어스 공에너지 ≈ |∬ r di_d di_q|  (사다리꼴 적분)
    spurious_J = abs(np.trapz(np.trapz(r, iq_1d, axis=1), id_1d))

    finite = np.isfinite(r)
    print("\n── 가역성 잔차 r = ∂λd/∂iq − ∂λq/∂id ──")
    print(f"  max|r|   = {np.nanmax(np.abs(r))*1e3:.3f} mH")
    print(f"  RMS r    = {np.sqrt(np.nanmean(r[finite]**2))*1e3:.3f} mH")
    print(f"  mean|∂λd/∂iq| = {np.nanmean(np.abs(dLd_diq))*1e3:.3f} mH")
    print(f"  mean|∂λq/∂id| = {np.nanmean(np.abs(dLq_did))*1e3:.3f} mH")
    print(f"  상대 잔차 중앙값 = {np.nanmedian(rel[finite]):.1f} %")
    print(f"  스퓨리어스 공에너지 |∬r| = {spurious_J:.2f} J")

    # ── 그림 ─────────────────────────────────────────────────────────────
    plt.rcParams.update({"font.size": 8, "figure.dpi": 130})
    fig, ax = plt.subplots(1, 3, figsize=(13.0, 3.8))
    fig.suptitle("Flux-map reciprocity residual  (e10_SatuMap)  "
                 "-- paper2 Phase B", fontsize=11, fontweight="bold")
    ID, IQ = np.meshgrid(id_1d, iq_1d, indexing="ij")

    def show(a, Z, title, cmap, sym=False):
        if sym:
            v = np.nanmax(np.abs(Z))
            cs = a.pcolormesh(ID, IQ, Z, cmap=cmap, vmin=-v, vmax=v,
                              shading="auto")
        else:
            cs = a.pcolormesh(ID, IQ, Z, cmap=cmap, shading="auto")
        fig.colorbar(cs, ax=a, shrink=0.9)
        a.set_title(title, fontsize=9)
        a.set_xlabel("i_d [A_pk]")
        a.set_ylabel("i_q [A_pk]")

    show(ax[0], dLd_diq * 1e3, "∂λd/∂iq  [mH]", "viridis")
    show(ax[1], dLq_did * 1e3, "∂λq/∂id  [mH]", "viridis")
    show(ax[2], r * 1e3, "residual r  [mH]  (=0 if conservative)",
         "RdBu_r", sym=True)

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out_png = OUT_DIR / "reciprocity_residual.png"
    fig.savefig(out_png)
    plt.close(fig)

    # ── 리포트 ───────────────────────────────────────────────────────────
    lines = [
        "# Phase B -- 자속맵 가역성 잔차 (task B1)", "",
        "e10_SatuMap.mat의 λ_d, λ_q에서 교차미분 잔차 "
        "`r = ∂λ_d/∂i_q − ∂λ_q/∂i_d` 를 계산. 보존 공에너지가 존재하면 r=0.", "",
        f"- 격자: {id_1d.size} × {iq_1d.size} (id × iq), 2사분면(id≤0, iq≥0)",
        f"- **max|r| = {np.nanmax(np.abs(r))*1e3:.3f} mH**, "
        f"RMS = {np.sqrt(np.nanmean(r[finite]**2))*1e3:.3f} mH",
        f"- 상호인덕턴스 규모 mean|∂λd/∂iq|={np.nanmean(np.abs(dLd_diq))*1e3:.2f} "
        f"mH, mean|∂λq/∂id|={np.nanmean(np.abs(dLq_did))*1e3:.2f} mH",
        f"- 상대 잔차(중앙값) = {np.nanmedian(rel[finite]):.1f} %",
        f"- **스퓨리어스 공에너지 |∬ r di_d di_q| = {spurious_J:.2f} J** "
        "(한 사이클 최대 에너지 누설 규모)",
        "",
        "## 함의",
        "- r≠0 이면 λ_d,λ_q 독립보간이 비보존장 -> 과도 MIL에서 저장에너지 "
        "항이 경로의존, 순시 전력수지 위반.",
        "- **Phase B 처방**: 단일 공에너지 W'(i_d,i_q)에서 λ 재구성(∇W' 최소자승) "
        "또는 Helmholtz 투영으로 curl-free 성분만 유지 -> r≡0 강제.",
        "- 재구성 후 정상상태 토크/효율 변화가 작아야(FEA 정합 유지) 하며, "
        "이는 A2 효율맵을 재계산해 확인 (Phase B 검증).",
        "",
        "> 주의: e10_SatuMap은 6×8 저해상도라 유한차분 잔차에 이산화 오차가 "
        "섞인다. 정밀 정량화는 고해상도 SatuMap 재수집 시 갱신.",
        "",
    ]
    rep = OUT_DIR / "PhaseB_reciprocity_report.md"
    rep.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n그림:   {out_png}")
    print(f"리포트: {rep}")


if __name__ == "__main__":
    main()
