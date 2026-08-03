# -*- coding: utf-8 -*-
"""Zenodo 기탁 목록 생성 — 파일·크기·SHA256.

담는 것 = 재현 패키지(GitHub)가 담지 않는 1차 기록.

  (1) 운전점별 FEA export  `_txt_backfill/<model>/<OP>/FEA_data.txt.gz`
      논문의 모든 수치가 여기서 나온다. Map_Summary JSON 이 이것의 축약이다.
      FullFEA = TS-FEA 진리값, Hybrid = 하이브리드 예측. 모델당 120 운전점씩.
  (2) MotorLAB 효율맵 원본 `.mat`
  (3) Motor-CAD 기계 모델 `.mot` (라이선스 서버 주소는 제거하고 기탁)

⚠️ `map_exports/e10/fields/*.txt` 는 담지 않는다 — (1)의 압축을 푼 사본이라
   중복이다. 헤더까지 동일함을 확인했다 (2026-08-03).

HalfSC 제외는 저자 결정(2026-08-03): 셋 다 담으면 53 GB 로 Zenodo 레코드당
50 GB 한도를 넘는다. Ref(k_r=1)와 SC(k_r=2)가 축척 패밀리의 양 끝이자 도너→
타깃 전달의 두 축이라 이 둘로 방법의 1차 기록이 성립한다. HalfSC 는 보간
검증이며, 그 요약(Map_Summary)은 재현 패키지에 그대로 공개된다.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKFILL = r"D:\KangDH\Thesis\e10\_txt_backfill"
THESIS = r"D:\KangDH\Thesis\e10"
E10 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "map_exports", "e10")
OUT = r"E:\KDH\Overleaf\JEET-2024_rev1\zenodo_manifest.txt"

MODELS = ("Ref", "SC")          # HalfSC 제외 — 위 docstring 참조

# 논문 3기 + Lab30 재빌드 3종. 치수로 확인함(고정자 외경 198/297/396 mm).
MOT = [
    ("models/e10_Ref_kr1.mot", "refModel/e10Turn6V261.mot"),
    ("models/e10_HalfSC_kr1p5.mot", "SLFEA_Half/e10Turn6V261SLFEA_Half.mot"),
    ("models/e10_SC_kr2.mot", "SLFEA/e10Turn6V261SLFEA.mot"),
    ("models/e10_Ref_Lab30.mot", "refModel/e10Turn6V261_Lab30.mot"),
    ("models/e10_SC_hybrid_Lab30.mot", "SLFEA/e10Turn6V261SLFEA_Lab30.mot"),
    ("models/e10_SC_fullfea_Lab30.mot",
     "SLFEA/e10Turn6V261SLFEA_FullFEA_Lab30.mot"),
]


STAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "map_exports", "_zenodo_stage")

# 공개 기탁 전 .mot 에서 비우는 줄. 라이선스 서버 호스트와 편집 이력에
# 내부 IP 가 그대로 실려 있다. `Previous_Version[n]` 은 "user 1055@<IP> ..." 형태.
# 주의: `K_Radial_User`, `UserCopperLossRatio_*` 등은 물리 파라미터다 — 건드리지
# 않도록 완전 일치와 접두사 일치만 쓴다(부분 문자열 금지).
SCRUB_EXACT = ("Licence_Name_Line1", "Licence_Name_Line2", "User")
SCRUB_PREFIX = ("Previous_Version",)


def scrub_mot(src, dst):
    """라이선스 서버·사용자·이력 줄을 비운 사본 (원본은 건드리지 않는다)."""
    out, hit = [], 0
    for ln in io.open(src, encoding="latin-1", newline=""):
        if "=" in ln:
            k = ln.split("=", 1)[0].strip()
            if k in SCRUB_EXACT or k.startswith(SCRUB_PREFIX):
                ln = "%s=\r\n" % k
                hit += 1
        out.append(ln)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    io.open(dst, "w", encoding="latin-1", newline="").write("".join(out))
    return hit


def digest(path, algo=hashlib.sha256, buf=1 << 22):
    h = algo()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(buf), b""):
            h.update(b)
    return h.hexdigest()


def collect():
    """[(기탁 이름, 원본 경로, 바이트)] — 이름은 레코드 안에서 유일해야 한다."""
    rows = []
    for m in MODELS:
        root = os.path.join(BACKFILL, m)
        if not os.path.isdir(root):
            print("  (없음) %s" % root)
            continue
        for op in sorted(os.listdir(root)):
            src = os.path.join(root, op, "FEA_data.txt.gz")
            if os.path.exists(src):
                rows.append(("fea/%s_%s.txt.gz" % (m, op), src,
                             os.path.getsize(src)))
    eff = os.path.join(E10, "effmaps")
    for f in sorted(os.listdir(eff)):
        if f.endswith(".mat"):
            src = os.path.join(eff, f)
            rows.append(("effmaps/" + f, src, os.path.getsize(src)))
    for name, rel in MOT:
        src = os.path.join(THESIS, *rel.split("/"))
        if not os.path.exists(src):
            print("  (없음) %s" % src)
            continue
        # 원본이 아니라 세정본을 기탁한다 — 해시도 세정본 기준이어야 한다
        dst = os.path.join(STAGE, os.path.basename(name))
        n = scrub_mot(src, dst)
        print("     %s  라이선스/사용자 %d줄 제거" % (os.path.basename(name), n))
        rows.append((name, dst, os.path.getsize(dst)))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-hash", action="store_true",
                    help="SHA256 생략 (목록·크기만 — 빠른 확인용)")
    a = ap.parse_args()

    rows = collect()
    total = sum(n for _, _, n in rows)
    groups = {}
    for name, _, n in rows:
        g = name.split("/")[0]
        c0, n0 = groups.get(g, (0, 0))
        groups[g] = (c0 + 1, n0 + n)
    for g, (c, n) in sorted(groups.items()):
        print("  %-10s %4d개  %8.2f GB" % (g, c, n / 2 ** 30))
    print("  %-10s %4d개  %8.2f GB\n" % ("합계", len(rows), total / 2 ** 30))

    if total > 50 * 2 ** 30:
        print("  [!] Zenodo 레코드당 기본 한도 50 GB 초과 — 분할이 필요하다.\n")

    lines, done = [], 0
    for i, (name, src, n) in enumerate(rows, 1):
        h = "-" * 64 if a.no_hash else digest(src)
        lines.append("%s  %14d  %s" % (h, n, name))
        done += n
        if not a.no_hash and (i % 40 == 0 or i == len(rows)):
            print("    해시 %d/%d  (%.1f/%.1f GB)"
                  % (i, len(rows), done / 2 ** 30, total / 2 ** 30))

    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# Zenodo deposit manifest\n")
        fh.write("# %d files, %.2f GB%s\n\n"
                 % (len(rows), total / 2 ** 30,
                    "  (SHA256 생략)" if a.no_hash else ""))
        fh.write("\n".join(lines) + "\n")
    print("\n목록: %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
