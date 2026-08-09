# -*- coding: utf-8 -*-
"""Fig 2: 단일 슬롯 TS-FEA 실측 Je vs Hybrid 참고 재구성 Je.

배치 규칙(feedback_jeet_artifact_placement 메모리와 동일):
  그림(PNG)      -> E:\\KDH\\Overleaf\\JEET-2024_rev1\\fig\\
  GIF·원본 데이터 -> J:\\내 드라이브\\EveryMotor_JEET_data\\results\\
  코드            -> eMach\\tools\\jeet_acloss_rbf (본 스크립트는 얇은 러너)

전 주기(128 Solution 블록) TS-FEA/Hybrid 텍스트가 이미 있어야 한다
(없으면 run_field_export.py 로 먼저 만들 것 --no-solve, 전체 스텝).

  python run_fig2_slot.py [--slot 1] [--step 70] [--skip-gif]
"""
import argparse
import json
import os
import sys

# 출력 폴더는 JEET_FIGDIR 로 덮어쓸 수 있다 (배포 레포/CI 용).
_FIGDIR = os.environ.get('JEET_FIGDIR', r'E:\KDH\Overleaf\JEET-2024_rev1\fig')

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "tools")))  # 이 체크아웃의 tools

import matplotlib
matplotlib.use("Agg")

from jeet_acloss_rbf import (plot_fig2_slot_comparison, plot_fig2_slot_rms,
                             make_fig2_slot_gif,
                             plot_fig_b_slot_comparison, make_fig_b_slot_gif)

FIELDS = (r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET"
          r"\map_exports\e10\fields")
TS_PATH = os.path.join(FIELDS, "Magnetic_Ref_ARCHIVE_460A_36deg_"
                       "OnLoadTorque.txt")
HY_PATH = os.path.join(FIELDS, "Magnetic_Ref_Hybrid_ARCHIVE_460A_36deg_"
                       "full_OnLoadTorque.txt")

FIG_OUT = os.path.join(_FIGDIR, 'fig2_slot_je_comparison.png')
DRIVE_DIR = r"J:\내 드라이브\EveryMotor_JEET_data\results"
DATA_JSON = os.path.join(DRIVE_DIR, "fig2_slot_je_static_data.json")
GIF_OUT = os.path.join(DRIVE_DIR, "fig2_slot_je_comparison.gif")
GIF_SUMMARY = os.path.join(DRIVE_DIR, "fig2_slot_je_gif_summary.json")
MANIFEST = os.path.join(DRIVE_DIR, "fig2_slot_je_MANIFEST.md")

# B 필드(슬롯 내부 전체 메시) 산출물
B_FIG_OUT = os.path.join(_FIGDIR, 'fig2_slot_b_comparison.png')
B_DATA_JSON = os.path.join(DRIVE_DIR, "fig2_slot_b_static_data.json")
B_GIF_OUT = os.path.join(DRIVE_DIR, "fig2_slot_b_comparison.gif")
B_GIF_SUMMARY = os.path.join(DRIVE_DIR, "fig2_slot_b_gif_summary.json")

# 주기-RMS 판 (순시 스냅샷 비교의 정의 불일치를 해소한 버전)
RMS_FIG_OUT = (r"E:\KDH\Overleaf\JEET-2024_rev1\fig"
               r"\fig2_slot_je_rms_comparison.png")
RMS_JSON = os.path.join(DRIVE_DIR, "fig2_slot_je_rms_summary.json")

FREQ_HZ = 1066.67          # 16000 rpm, 8극 -> f_e = rpm/60 * P/2


def write_manifest(static_data, gif_summary):
    lines = [
        "# Fig 2 (slot Je comparison) 산출물 위치",
        "",
        "자동 생성 (`run_fig2_slot.py`). 배치 규칙: 그림→Overleaf `fig/`,",
        "GIF·데이터→Drive JSON, 코드→eMach 패키지.",
        "",
        "| 산출물 | 위치 | 생성 함수 |",
        "|---|---|---|",
        "| 정적 2-패널 PNG (최종 논문용) | `%s` | "
        "`manuscript_figs.plot_fig2_slot_comparison` |" % FIG_OUT,
        "| 정적 그림의 원본 필드 데이터 | `%s` | 위와 동일 (반환값 저장) |"
        % DATA_JSON,
        "| 128스텝 동기 애니메이션 GIF | `%s` | "
        "`manuscript_figs.make_fig2_slot_gif` |" % GIF_OUT,
        "| GIF 스텝별 \\|Je\\|max 요약 | `%s` | 위와 동일 |" % GIF_SUMMARY,
        "| 슬롯 내부 전체 메시 \\|B\\| PNG | `%s` | "
        "`manuscript_figs.plot_fig_b_slot_comparison` |" % B_FIG_OUT,
        "| \\|B\\| 그림의 원본 필드 데이터 | `%s` | 위와 동일 |"
        % B_DATA_JSON,
        "| \\|B\\| 128스텝 GIF | `%s` | "
        "`manuscript_figs.make_fig_b_slot_gif` |" % B_GIF_OUT,
        "| \\|B\\| 스텝별 요약 | `%s` | 위와 동일 |" % B_GIF_SUMMARY,
        "",
        "`--only-b` 로 B 산출물만 따로 생성할 수 있다. Je 는 두 패널이"
        " TS-FEA 도체 메시를 공유하지만, B 는 두 해석 모두 자기 메시에서"
        " 실제로 푼 값이라 각자 자기 메시에 그린다.",
        "",
        "## 원본 전 주기 export (입력)",
        "",
        "| 파일 | 내용 |",
        "|---|---|",
        "| `%s` | TS-FEA(FullFEA), Ref, 460 A, 36 deg, 128블록 |" % TS_PATH,
        "| `%s` | Hybrid(MS-FEA), Ref, 460 A, 36 deg, 128블록 |" % HY_PATH,
        "",
        "## 채택 시점",
        "",
        "- 슬롯: %d" % static_data["slot_id"],
        "- 정적 그림 스텝: %d / %d (rotate %.2f deg)"
        % (static_data["step"], gif_summary["n_frames"],
           static_data["rotate_deg"]),
        "- 선정 근거: 128스텝 전체 스캔에서 이 슬롯 |Je| 전역 최댓값 지점"
        " (%.1f A/mm2)" % static_data["vlim_A_mm2"],
        "- 공극 방향: 그림 아래쪽(`airgap_side='bottom'`)",
        "",
        "## 재현 방법",
        "",
        "```python",
        "from jeet_acloss_rbf import plot_fig2_slot_comparison, "
        "make_fig2_slot_gif",
        "plot_fig2_slot_comparison(TS_PATH, HY_PATH, FIG_OUT, slot_id=%d,"
        % static_data["slot_id"],
        "                          step=%d, freq_hz=%.2f)"
        % (static_data["step"], FREQ_HZ),
        "make_fig2_slot_gif(TS_PATH, HY_PATH, GIF_OUT, slot_id=%d,"
        % static_data["slot_id"],
        "                   freq_hz=%.2f, out_json=GIF_SUMMARY)" % FREQ_HZ,
        "```",
    ]
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("매니페스트 저장:", MANIFEST)


def run_b_field(a):
    """슬롯 내부 전체 메시 |B| 그림·GIF (TS-FEA vs MS-FEA)."""
    print("=== B 정적 2-패널 (step %d) ===" % a.step)
    b_static = plot_fig_b_slot_comparison(
        TS_PATH, HY_PATH, B_FIG_OUT, slot_id=a.slot, step=a.step,
        airgap_side=a.airgap_side)
    os.makedirs(DRIVE_DIR, exist_ok=True)
    with open(B_DATA_JSON, "w", encoding="utf-8") as fh:
        json.dump(b_static, fh, ensure_ascii=False, indent=1)
    print("B 데이터 JSON (Drive):", B_DATA_JSON)

    if a.skip_gif:
        print("--skip-gif 지정: B GIF 생략")
        return b_static, None

    print("\n=== B 128스텝 동기 GIF ===")
    b_gif = make_fig_b_slot_gif(
        TS_PATH, HY_PATH, B_GIF_OUT, slot_id=a.slot,
        airgap_side=a.airgap_side, out_json=B_GIF_SUMMARY)
    return b_static, b_gif


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", type=int, default=1)
    ap.add_argument("--step", type=int, default=70)
    ap.add_argument("--airgap-side", default="bottom")
    ap.add_argument("--skip-gif", action="store_true")
    ap.add_argument("--only-b", action="store_true",
                    help="B 필드 그림만 생성 (Je 생략)")
    ap.add_argument("--only-rms", action="store_true",
                    help="주기-RMS Je 그림만 생성")
    a = ap.parse_args()

    if a.only_b:
        run_b_field(a)
        return
    if a.only_rms:
        plot_fig2_slot_rms(TS_PATH, HY_PATH, RMS_FIG_OUT, slot_id=a.slot,
                           freq_hz=FREQ_HZ, airgap_side=a.airgap_side,
                           out_json=RMS_JSON)
        print("RMS Fig PNG (Overleaf):", RMS_FIG_OUT)
        return

    print("=== 정적 2-패널 (step %d) ===" % a.step)
    static_data = plot_fig2_slot_comparison(
        TS_PATH, HY_PATH, FIG_OUT, slot_id=a.slot, step=a.step,
        freq_hz=FREQ_HZ, airgap_side=a.airgap_side, show_titles=True)
    print("Fig PNG (Overleaf):", FIG_OUT)

    os.makedirs(DRIVE_DIR, exist_ok=True)
    with open(DATA_JSON, "w", encoding="utf-8") as fh:
        json.dump(static_data, fh, ensure_ascii=False, indent=1)
    print("데이터 JSON (Drive):", DATA_JSON)

    if a.skip_gif:
        print("--skip-gif 지정: GIF 생략")
        return

    print("\n=== 128스텝 동기 GIF ===")
    gif_summary = make_fig2_slot_gif(
        TS_PATH, HY_PATH, GIF_OUT, slot_id=a.slot, freq_hz=FREQ_HZ,
        airgap_side=a.airgap_side, out_json=GIF_SUMMARY)
    print("GIF (Drive):", GIF_OUT)

    write_manifest(static_data, gif_summary)


if __name__ == "__main__":
    main()
