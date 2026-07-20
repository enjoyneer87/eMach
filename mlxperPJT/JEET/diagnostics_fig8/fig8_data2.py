# -*- coding: utf-8 -*-
"""Fig 8 데이터 완결성 - 정확판 (mode/phase/TS 필드 실제 키 사용)"""
import json, os
from collections import Counter, defaultdict

BASE = r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports\e10"
FILES = {
    "Ref":    os.path.join(BASE, "Ref", "JEET_ACLoss_Ref_Map_Summary.json"),
    "HalfSC": os.path.join(BASE, "HalfSC", "JEET_ACLoss_HalfSC_Map_Summary.json"),
    "SC":     os.path.join(BASE, "SC", "JEET_ACLoss_SC_Map_Summary.json"),
}

for model, f in FILES.items():
    print("=" * 74)
    print(f"### {model}")
    with open(f, encoding="utf-8") as fh:
        recs = json.load(fh)
    if isinstance(recs, dict):
        for k in ("records", "data", "results"):
            if k in recs:
                recs = recs[k]; break
    print(f"  레코드 {len(recs)}")
    print(f"  전체 키: {sorted(recs[0].keys())}")

    modes = Counter(r.get("mode") for r in recs)
    print(f"  mode 분포: {dict(modes)}")

    # TS 손실로 쓸만한 키 후보 탐색
    cand = [k for k in recs[0].keys()
            if any(t in k.lower() for t in ("ts_", "fea_total", "_ts", "tsfea"))]
    print(f"  TS 후보 키: {cand}")

    # 운전점(속도·전류·위상) 유니크 수
    pts = set((r.get("speed"), r.get("current"), r.get("phase")) for r in recs)
    print(f"  유니크 운전점: {len(pts)}")

    # mode별 운전점
    bym = defaultdict(set)
    for r in recs:
        bym[r.get("mode")].add((r.get("speed"), r.get("current"), r.get("phase")))
    for m, s in bym.items():
        print(f"    mode={m}: {len(s)}점")

    # 위상 분포
    ph = sorted(set(r.get("phase") for r in recs if r.get("phase") is not None))
    print(f"  위상 {len(ph)}종: {ph}")

    # TS 값 유효성
    for k in cand:
        vals = [r.get(k) for r in recs]
        ok = sum(1 for v in vals if isinstance(v, (int, float)) and v == v and v != 0)
        print(f"    {k}: 유효 {ok}/{len(vals)}")
