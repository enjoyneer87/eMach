# -*- coding: utf-8 -*-
"""파이프라인 기준 모델별 데이터셋 점수 확인 (논문 74/82/89 대조)"""
import sys, os
sys.path.insert(0, r"D:\KangDH\EveryMotor\eMach\tools")

import matplotlib
matplotlib.use("Agg")

from jeet_acloss_rbf.pipeline import AcLossPipeline

PAPER = {"Ref": 74, "HalfSC": 82, "SC": 89}

pl = AcLossPipeline()
print("DEFAULT_CONFIG 키:", sorted(getattr(pl, "config", {}).keys())[:20])
print()

for model in ("Ref", "HalfSC", "SC"):
    print("=" * 70)
    try:
        ds = pl.load_dataset(model)
    except Exception as e:
        print(f"### {model}: load_dataset 실패 - {type(e).__name__}: {e}")
        continue
    try:
        st = pl.dataset_struct(ds)
    except Exception:
        st = None
    n = None
    for attr in ("af", "AF", "y", "target"):
        v = ds.get(attr) if isinstance(ds, dict) else getattr(ds, attr, None)
        if v is not None:
            try:
                n = len(v)
                break
            except Exception:
                pass
    if n is None and isinstance(ds, dict):
        for k, v in ds.items():
            try:
                n = len(v); print(f"  (길이는 '{k}' 기준)"); break
            except Exception:
                continue
    print(f"### {model}: 데이터셋 점수 = {n}   (논문 표기 {PAPER[model]})")
    if isinstance(ds, dict):
        print(f"  키: {sorted(ds.keys())[:14]}")
        for k in ("speed", "i_rms", "beta", "current", "phase"):
            v = ds.get(k)
            if v is not None:
                try:
                    import numpy as np
                    u = sorted(set(np.asarray(v).ravel().tolist()))
                    print(f"  {k} ({len(u)}종): {u[:10]}")
                except Exception:
                    pass
    if st is not None:
        print(f"  dataset_struct: {st if not hasattr(st,'keys') else {k: st[k] for k in list(st)[:8]}}")
