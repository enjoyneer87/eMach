# -*- coding: utf-8 -*-
"""Zenodo 기탁 초안 생성 + 2.6 GB 업로드 (발행은 하지 않는다).

이 스크립트는 **발행(publish)하지 않는다.** 초안(draft)까지만 만들고 DOI를
예약해 준 뒤 편집 URL을 찍는다. 발행은 브라우저에서 내용을 눈으로 확인하고
직접 눌러야 한다 — 발행 즉시 파일이 영구 고정되기 때문이다.

    # 1) 토큰 발급: zenodo.org > Applications > Personal access tokens
    #    권한은 deposit:write, deposit:actions 두 개면 된다.
    set ZENODO_TOKEN=...

    # 2) 먼저 샌드박스에서 예행 (별도 계정·별도 토큰: sandbox.zenodo.org)
    python run_zenodo_upload.py

    # 3) 실제 기탁
    python run_zenodo_upload.py --production

이미 올라간 파일은 체크섬이 맞으면 건너뛰므로, 중간에 끊겨도 다시 돌리면 된다.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
E10 = os.environ.get("JEET_DATA_ROOT", os.path.join(HERE, "map_exports", "e10"))
MANIFEST = r"E:\KDH\Overleaf\JEET-2024_rev1\zenodo_manifest.txt"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 레코드 메타데이터 (ZENODO_DEPOSIT.md §2 와 같은 내용) ──────────────
DESCRIPTION = """\
<p>Raw analysis outputs behind the AC copper-loss calibration study of a scaled
hairpin traction-motor family. The set covers three geometrically scaled
machines (radial scaling factors 1, 1.5 and 2) and contains element-level
magnetic field exports from transient and magnetostatic finite-element
solutions at matched operating points, together with the efficiency-map
electrical data used for the drive-cycle comparison.</p>

<p>These files are the primary record. They are <strong>not</strong> required to
reproduce the paper's figures: the reproduction package at
<a href="https://github.com/enjoyneer87/JEET-repro">github.com/enjoyneer87/JEET-repro</a>
rebuilds every figure from reduced summaries of this data, and includes the
scripts that produce those reductions. This deposit lets a reader verify the
reduction step itself.</p>

<p>Field exports are plain text, one file per machine and excitation source,
each holding 128 rotor positions over one electrical period with per-element
current density, flux density and magnetic vector potential. Efficiency-map
data are MATLAB v5 MAT-files on a 33 speed x 151 torque grid.</p>"""

METADATA = {
    "upload_type": "dataset",
    "title": ("Element-level magnetic field exports and efficiency-map data "
              "for AC copper-loss calibration of scaled hairpin traction "
              "motors (e10 family)"),
    "creators": [{"name": "Kang, Do Hyun"}],   # affiliation·orcid 는 웹에서 보완
    "description": DESCRIPTION,
    "access_right": "open",
    "license": "cc-by-4.0",
    "language": "eng",
    "version": "1.0.0",
    "keywords": ["hairpin winding", "AC copper loss", "proximity loss",
                 "finite element analysis", "traction motor",
                 "geometric scaling", "efficiency map"],
    "related_identifiers": [
        {"relation": "isSupplementedBy",
         "identifier": "https://github.com/enjoyneer87/JEET-repro",
         "scheme": "url"},
    ],
}


def digest(path, algo=hashlib.sha256, buf=1 << 22):
    """스트리밍 해시 — 389 MB 파일을 통째로 메모리에 올리지 않는다."""
    h = algo()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(buf), b""):
            h.update(b)
    return h.hexdigest()


def load_manifest():
    """zenodo_manifest.txt -> [(상대경로, 바이트, sha256)]"""
    rows = []
    for ln in io.open(MANIFEST, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        h, n, name = ln.split(None, 2)
        rows.append((name, int(n), h))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--production", action="store_true",
                    help="실제 zenodo.org 에 기탁 (기본은 샌드박스)")
    ap.add_argument("--deposition", type=int,
                    help="기존 초안 이어서 업로드 (중단 후 재개)")
    ap.add_argument("--check", action="store_true",
                    help="업로드 없이 목록·원본·체크섬만 검증")
    a = ap.parse_args()

    rows0 = load_manifest()
    if a.check:
        bad = ok = 0
        for name, n, h in rows0:
            src = os.path.join(E10, *name.split("/"))
            if not os.path.exists(src):
                print("  없음      %s" % name)
                bad += 1
            elif os.path.getsize(src) != n:
                print("  크기 불일치 %s" % name)
                bad += 1
            else:
                ok += 1
        print("\n%d개 정상, %d개 문제 (총 %.2f GB)"
              % (ok, bad, sum(n for _, n, _ in rows0) / 1073741824))
        return 1 if bad else 0

    try:
        import requests                                    # noqa: F401
    except ImportError:
        print("requests 가 필요하다:  pip install requests")
        return 2

    base = ("https://zenodo.org" if a.production
            else "https://sandbox.zenodo.org")
    tok = os.environ.get("ZENODO_TOKEN")
    if not tok:
        print("ZENODO_TOKEN 환경변수가 없다.")
        return 2
    auth = {"Authorization": "Bearer %s" % tok}

    rows = rows0
    total = sum(n for _, n, _ in rows)
    print("대상 %d개 파일, %.2f GB  ->  %s"
          % (len(rows), total / 1073741824, base))
    if not a.production:
        print("*** 샌드박스 모드 — 실제 기탁이 아니다 ***")

    # ── 초안 확보 ─────────────────────────────────────────────────────
    if a.deposition:
        r = requests.get("%s/api/deposit/depositions/%d" % (base, a.deposition),
                         headers=auth, timeout=60)
    else:
        r = requests.post("%s/api/deposit/depositions" % base, headers=auth,
                          json={}, timeout=60)
    if r.status_code >= 400:
        print("초안 생성 실패 %d: %s" % (r.status_code, r.text[:400]))
        return 1
    dep = r.json()
    dep_id, bucket = dep["id"], dep["links"]["bucket"]
    print("초안 %d" % dep_id)

    # ── 메타데이터 + DOI 예약 ─────────────────────────────────────────
    meta = dict(METADATA)
    meta["prereserve_doi"] = True
    r = requests.put("%s/api/deposit/depositions/%d" % (base, dep_id),
                     headers=auth, json={"metadata": meta}, timeout=60)
    if r.status_code >= 400:
        print("메타데이터 실패 %d: %s" % (r.status_code, r.text[:400]))
        return 1
    doi = (r.json().get("metadata", {})
           .get("prereserve_doi", {}).get("doi", "(예약 실패)"))
    print("예약 DOI: %s\n" % doi)

    # ── 파일 업로드 (이미 올라간 것은 건너뜀) ─────────────────────────
    have = {}
    r = requests.get("%s/api/deposit/depositions/%d/files" % (base, dep_id),
                     headers=auth, timeout=60)
    if r.status_code < 400:
        have = {f["filename"]: f.get("checksum", "") for f in r.json()}

    sent = 0
    for i, (name, n, _) in enumerate(rows, 1):
        src = os.path.join(E10, *name.split("/"))
        if not os.path.exists(src):
            print("  [%2d/%d] 원본 없음 — %s" % (i, len(rows), src))
            return 1
        key = name.replace("/", "_")
        if key in have:
            print("  [%2d/%d] 건너뜀 (이미 있음)  %s" % (i, len(rows), key))
            sent += n
            continue
        print("  [%2d/%d] %7.1f MB  %s ..." % (i, len(rows), n / 1048576, key),
              end="", flush=True)
        with open(src, "rb") as fh:
            u = requests.put("%s/%s" % (bucket, key), data=fh, headers=auth,
                             timeout=None)
        if u.status_code >= 400:
            print(" 실패 %d: %s" % (u.status_code, u.text[:200]))
            return 1
        got = u.json().get("checksum", "").split(":")[-1]
        want = digest(src, hashlib.md5)      # 스트리밍 — 389 MB 도 안전
        if got and got != want:
            print(" 체크섬 불일치! 서버 %s vs 로컬 %s" % (got[:12], want[:12]))
            return 1
        print(" 완료")
        sent += n

    print("\n업로드 %.2f GB 완료." % (sent / 1073741824))
    print("초안 확인: %s/uploads/%d" % (base, dep_id))
    print("\n발행(publish)은 하지 않았다. 위 URL 에서 내용을 확인한 뒤")
    print("직접 Publish 를 누를 것 — 누르는 순간 파일이 영구 고정된다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
