# -*- coding: utf-8 -*-
"""Zenodo 업로드 목록 생성 — 파일·크기·SHA256.

담는 것 = 재현 패키지가 담지 않는 1차 기록.
  (1) 전주기 필드 export (Motor-CAD/JMAG 원본 텍스트)
  (2) Motor-CAD 기계 모델 .mot
  (3) MotorLAB 효율맵 원본 .mat
재현 패키지(GitHub)는 이들의 축약본만 담으므로, Zenodo 쪽은 provenance 용도다.
"""
import hashlib
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

E10 = r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports\e10"

GROUPS = [
    ("fields/", "전주기 자계 요소 export (Motor-CAD 텍스트)",
     os.path.join(E10, "fields"), (".txt",)),
    ("effmaps/", "MotorLAB 효율맵 원본",
     os.path.join(E10, "effmaps"), (".mat",)),
]


def sha256(p, buf=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            b = fh.read(buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


rows, grand = [], 0
for tag, desc, root, exts in GROUPS:
    if not os.path.isdir(root):
        print("  (없음) %s" % root)
        continue
    files = sorted(f for f in os.listdir(root)
                   if os.path.splitext(f)[1].lower() in exts)
    sub = 0
    print("\n== %s — %s (%d개)" % (tag, desc, len(files)))
    for f in files:
        p = os.path.join(root, f)
        n = os.path.getsize(p)
        sub += n
        rows.append((tag + f, n, sha256(p)))
        print("   %8.1f MB  %s" % (n / 1048576, f))
    grand += sub
    print("   %8.1f MB  소계" % (sub / 1048576))

print("\n총 %.2f GB / %d개 파일" % (grand / 1073741824, len(rows)))

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "zenodo_manifest.txt")
with io.open(out, "w", encoding="utf-8") as fh:
    fh.write("# Zenodo deposit manifest\n")
    fh.write("# %d files, %.2f GB\n\n" % (len(rows), grand / 1073741824))
    for name, n, h in rows:
        fh.write("%s  %14d  %s\n" % (h, n, name))
print("목록: %s" % out)
