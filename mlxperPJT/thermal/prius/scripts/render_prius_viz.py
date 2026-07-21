# -*- coding: utf-8 -*-
"""Prius 열해석 표준 시각화 드라이버.

thermal_viz 패키지로 워터재킷 저/고부하 결과에 **규격화된 GIF/PNG 세트**를 생성.
어떤 GIF/PNG를 뽑을지 여기서 데이터셋+규격으로 고정 → 재현성 확보.

실행:  python render_prius_viz.py [low|high|all]
"""
import os, sys, traceback

# thermal_viz.py 는 상위 thermal/ 폴더
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from thermal_viz import render_standard_viz, STANDARD_GIFS, STANDARD_PNGS

# MAPDL 결과 위치(세션 스크래치) — 필요시 경로만 갱신
RTH_ROOT = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\292f8893-fe65-44a6-9565-cb88503b2e90\scratchpad"
VIZ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "viz"))

# 데이터셋 규격: (키, rth, 출력폴더, 라벨, clim_lo[냉각수온])
DATASETS = {
    "low":  (os.path.join(RTH_ROOT, "real_37072", "file.rth"),
             os.path.join(VIZ_ROOT, "waterjacket_low"),  "Prius WJ LOW (Fluent-match)", 27.0),
    "high": (os.path.join(RTH_ROOT, "real_18456", "file.rth"),
             os.path.join(VIZ_ROOT, "waterjacket_high"), "Prius WJ HIGH (250A)", 27.0),
}
# Prius active-part 재료번호 (02_step_to_cdb 규약): 1 stator 2 magnet 3 coil 4 shaft 5 rotor
PRIUS_MATS = dict(stator=1, magnet=2, coil=3, shaft=4, rotor=5)
# 메시 단위는 미터(step2cdb에서 mm/1000). 활성스택 ±0.0419m → 긴 샤프트 돌출
# 트림해 깔끔한 반단면. 여유 0.045m(=45mm).
PRIUS_ZTRIM = 0.045


def wj_circuit_builder(tv):
    """워터재킷 열등가회로(08_mapdl_waterjacket 토폴로지)를 형상에 맞춰 배치.
    노드 위치는 tv.R/스택반길이로 스케일, 노드 온도는 실제 부품 최고온에서 도출."""
    R = tv.R
    zh = float(tv.solid.bounds[5])          # 활성 스택 반길이(트림 후)
    mx = tv._maxes(tv.Tend)                  # 부품별 최고온
    nodes = {
        "COOL":  (0.0,  1.35 * R, 0.0),                 # 냉각수(스테이터 OD)
        "GAP_S": (0.55 * R, 0.0,  0.35 * zh),           # 공극 스테이터측
        "GAP_R": (0.42 * R, 0.0, -0.35 * zh),           # 공극 로터측
        "SHF":   (0.0, 0.0, -(zh + 0.55 * R)),          # 샤프트(축 하단)
        "AIR":   (0.5 * R, 0.0,  zh + 0.55 * R),        # 내부공기(축 상단)
        "CEND":  (0.0, -0.9 * R,  zh + 0.35 * R),       # 코일엔드
    }
    edges = [("GAP_S", "GAP_R"), ("GAP_S", "COOL"), ("GAP_R", "SHF"),
             ("SHF", "AIR"), ("AIR", "CEND"), ("CEND", "COOL")]
    node_T = {"COOL": 27.0,
              "GAP_S": mx.get("stator"), "GAP_R": mx.get("rotor"),
              "SHF": mx.get("shaft", 90.0), "AIR": mx.get("coil"),
              "CEND": mx.get("coil")}
    return dict(nodes=nodes, edges=edges, node_T=node_T)


def run(key):
    rth, out, label, clo = DATASETS[key]
    if not os.path.exists(rth):
        print(f"[{key}] SKIP - rth 없음: {rth}"); return
    print(f"=== {key}: {label} ===")
    render_standard_viz(rth, out, label=label, clim_lo=clo, mats=PRIUS_MATS,
                        z_trim=PRIUS_ZTRIM, gifs=STANDARD_GIFS, pngs=STANDARD_PNGS,
                        circuit_builder=wj_circuit_builder, log=print)
    # 레거시 이름 호환: internal = 3d_cut
    import shutil
    src = os.path.join(out, "transient_3d_cut.gif")
    if os.path.exists(src):
        shutil.copy(src, os.path.join(out, "wj_transient_internal.gif"))
        print(f"  compat: wj_transient_internal.gif <- transient_3d_cut.gif")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    keys = list(DATASETS) if which == "all" else [which]
    try:
        for k in keys:
            run(k)
        print("DONE-OK")
    except Exception:
        traceback.print_exc()
    os._exit(0)
