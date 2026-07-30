# -*- coding: utf-8 -*-
"""e4a ref vs 변형체 .mot 전수 diff — 미스케일 길이 키 색출.

[Dimensions] 등 전 섹션의 숫자 키를 비교해
  (a) 비 ~1.0 (미스케일) 인 nonzero 키
  (b) 비가 1.0도 k_r도 아닌 (비정형) 키
를 섹션별로 나열한다. 각도/카운트/플래그성 이름은 제외.
"""
from __future__ import annotations

import io
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = r"D:\KangDH\Thesis\e4a\newfam_results"
REF = BASE + r"\e4a_EMobility_IPM_User.mot"
VAR = BASE + r"\e4a_SC.mot"
KR = 2.0

EXCLUDE = re.compile(
    r"Angle|Arc|Number|Layers|Paths|Poles|Slots|Turns|Strands|Type|Method|"
    r"Calc|Display|State|Option|Enable|Use|Mode|Definition|Spec|Choice|"
    r"Select|Index|Count|Version|Colour|Color|Temperature|Temp|Speed|"
    r"Current|Voltage|Frequency|Duty|Factor|Ratio|Grade|Density|Loss|"
    r"Resist|Induct|Weight|Cost|Segments|Offset_Elec|Phase", re.I)


def parse(path):
    out = {}
    sec = "?"
    for line in io.open(path, encoding="latin-1"):
        line = line.strip()
        m = re.match(r"^\[(.+)\]$", line)
        if m:
            sec = m.group(1)
            continue
        m = re.match(r"^([A-Za-z0-9_\[\]]+)=(-?[\d.]+(?:[eE][+-]?\d+)?)$",
                     line)
        if m:
            try:
                out[(sec, m.group(1))] = float(m.group(2))
            except ValueError:
                pass
    return out


ref = parse(REF)
var = parse(VAR)

unscaled, odd = [], []
for key, v0 in ref.items():
    sec, name = key
    if v0 == 0 or key not in var:
        continue
    if EXCLUDE.search(name):
        continue
    r = var[key] / v0
    if abs(r - 1.0) < 1e-6:
        # 정수 플래그성(작은 정수 동일값)은 노이즈 — 값 기준 필터
        if v0 == int(v0) and abs(v0) <= 20:
            continue
        unscaled.append((sec, name, v0))
    elif abs(r - KR) > 1e-3 and abs(r - KR**2) > 1e-3 \
            and abs(r - 1.0 / KR) > 1e-3 and abs(r - 1.0 / KR**2) > 1e-3:
        odd.append((sec, name, v0, var[key], r))

print("=== 비 1.0 (미스케일, nonzero, 비정수/큰값) ===")
cur = None
for sec, name, v0 in sorted(unscaled):
    if sec != cur:
        print(f"[{sec}]")
        cur = sec
    print(f"    {name:42s} = {v0:g}")

print("\n=== 비정형 비 (1, k_r, k_r^2, 1/k_r 아님) ===")
cur = None
for sec, name, v0, v1, r in sorted(odd):
    if sec != cur:
        print(f"[{sec}]")
        cur = sec
    print(f"    {name:42s} {v0:g} -> {v1:g}  (x{r:.4f})")
