# -*- coding: utf-8 -*-
"""AF 산출 가능 운전점 수를 직접 계산하고 배제 사유를 분류."""
import json, os
from collections import defaultdict

BASE = r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports\e10"
FILES = {
    "Ref":    (os.path.join(BASE, "Ref", "JEET_ACLoss_Ref_Map_Summary.json"), "hybrid_total_kW"),
    "HalfSC": (os.path.join(BASE, "HalfSC", "JEET_ACLoss_HalfSC_Map_Summary.json"), "hybrid_total_kW"),
    "SC":     (os.path.join(BASE, "SC", "JEET_ACLoss_SC_Map_Summary.json"), "fea_total_ac_kW"),
}
PAPER = {"Ref": 74, "HalfSC": 82, "SC": 89}

def val(r, *keys):
    for k in keys:
        v = r.get(k)
        if isinstance(v, (int, float)) and v == v:
            return float(v)
    return None

for model, (f, feakey) in FILES.items():
    print("=" * 74)
    print(f"### {model}")
    recs = json.load(open(f, encoding="utf-8"))
    byp = defaultdict(dict)
    for r in recs:
        key = (r.get("speed"), r.get("current"), r.get("phase"))
        byp[key][r.get("mode")] = r

    n_total = len(byp)
    n_zero = n_noh = n_nof = n_ok = 0
    miss_detail = []
    for key, d in byp.items():
        spd, cur, ph = key
        h = d.get("Hybrid"); fe = d.get("FullFEA")
        hv = val(h, "hybrid_total_kW") if h else None
        fv = val(fe, feakey, "hybrid_total_kW", "ts_ac_active_only_kW") if fe else None
        if cur is not None and float(cur) == 0.0:
            n_zero += 1
        elif hv is None or hv == 0:
            n_noh += 1; miss_detail.append(("hybrid없음", key))
        elif fv is None or fv == 0:
            n_nof += 1; miss_detail.append(("FEA없음", key))
        else:
            n_ok += 1

    print(f"  전체 운전점        : {n_total}")
    print(f"  무부하(I=0) 제외   : {n_zero}")
    print(f"  Hybrid 결손        : {n_noh}")
    print(f"  FullFEA 결손       : {n_nof}")
    print(f"  -> AF 산출 가능    : {n_ok}   (논문 표기 {PAPER[model]})")
    d = n_ok - PAPER[model]
    print(f"     차이            : {d:+d}")
    if miss_detail:
        print(f"  결손 상세(최대 12건):")
        for why, k in miss_detail[:12]:
            print(f"     {why}: speed={k[0]}, I={k[1]}, beta={k[2]}")
