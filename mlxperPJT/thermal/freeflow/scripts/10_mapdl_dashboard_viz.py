# -*- coding: utf-8 -*-
"""e10 FreeFlow(JAC279 하이브리드) 결과 표준 시각화 드라이버.
thermal_viz.render_standard_viz 재사용 + FreeFlow 오일냉각 회로빌더.
Prius render_prius_viz.py 와 동일 패턴. 출력=별도폴더(freeflow/viz/mapdl).
"""
import os, sys, traceback
sys.path.insert(0, r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal")
from thermal_viz import render_standard_viz, STANDARD_GIFS, STANDARD_PNGS

RTH = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\ff_hybrid_v2_run2\file.rth"
OUT = r"D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\viz\mapdl"
LOG = r"C:\Users\moa\AppData\Local\Temp\claude\d--KDH-NvidiaNemo\298544ad-ddbc-4058-ba12-169c3e37aff3\scratchpad\ff_dashboard.txt"
_l = open(LOG, "w", encoding="utf-8")
def P(*a): _l.write(" ".join(str(x) for x in a) + "\n"); _l.flush()

# e10 능동부 재료(v2 메시): 1 stator / 2 magnet / 3 winding / 4 shaft / 5 rotor
E10_MATS = dict(stator=1, magnet=2, coil=3, shaft=4, rotor=5)


def ff_circuit_builder(tv):
    """FreeFlow 오일냉각 열등가회로(OIL 공급 + JACKET 스파이럴자켓 + SPRAY 엔드턴스프레이
    + GAP 공극). 노드위치는 형상 반경/축중심 기준 배치, 온도는 부품최고온에서 도출."""
    R = tv.R
    b = tv.solid.bounds
    zc = 0.5 * (b[4] + b[5]); zh = 0.5 * (b[5] - b[4])   # 축중심/반길이(오프셋대응)
    def Z(f): return zc + f * zh

    nodes = {
        "OIL":    (0.0,  1.55 * R, Z(-1.25)),   # 오일 공급/섬프
        "JACKET": (0.0,  1.20 * R, Z(0.0)),     # 스파이럴 자켓(스테이터 OD)
        "SPRAY":  (0.0, -1.05 * R, Z(1.30)),    # 엔드턴 스프레이(축단)
        "GAP_S":  (0.62 * R, 0.0,  Z(0.25)),    # 공극-스테이터측
        "GAP_R":  (0.45 * R, 0.0,  Z(-0.25)),   # 공극-로터측
    }
    edges = [("OIL", "JACKET"), ("JACKET", "GAP_S"), ("GAP_S", "GAP_R"),
             ("GAP_R", "OIL"), ("OIL", "SPRAY"), ("SPRAY", "JACKET")]

    def node_T_fn(T):
        m = tv._maxes(T)
        st = m.get("stator"); wd = m.get("coil"); ro = m.get("rotor")
        # 오일측 노드는 냉각수 온도(금속보다 낮음): 솔브 최종비율(~0.27) 적용
        return {"OIL": 70.0,
                "JACKET": 70.0 + 0.26 * ((st or 70.0) - 70.0),
                "SPRAY":  70.0 + 0.27 * ((wd or 70.0) - 70.0),
                "GAP_S":  st, "GAP_R": ro}

    return dict(nodes=nodes, edges=edges,
                node_T=node_T_fn(tv.Tend), node_T_fn=node_T_fn)


try:
    if not os.path.exists(RTH):
        P("no rth:", RTH); raise SystemExit
    os.makedirs(OUT, exist_ok=True)
    P("rendering ->", OUT)
    render_standard_viz(RTH, OUT,
                        label="e10 FreeFlow JAC279-hybrid (oil jacket+spray, 460A/16000rpm)",
                        clim_lo=70.0, mats=E10_MATS, z_trim=None,
                        gifs=STANDARD_GIFS, pngs=STANDARD_PNGS,
                        circuit_builder=ff_circuit_builder, log=P)
    P("DONE-OK")
except SystemExit:
    P("SKIP")
except Exception:
    P("EXC:", traceback.format_exc())
finally:
    _l.close()
    os._exit(0)
