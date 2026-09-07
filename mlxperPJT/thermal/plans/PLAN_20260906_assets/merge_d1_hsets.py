# -*- coding: utf-8 -*-
"""merge_d1_hsets.py -- D1 의 base / sph 결과 JSON 두 개를 계획서가 요구하는 한 파일로 합친다.

왜 두 파일로 나뉘어 나오나
--------------------------
`d1_cont_rating.py` 는 SURF152 의 대류계수를 **ESURF 시점에 한 번** 써 넣는다.
한 세션 안에서 두 번째 h 세트로 바꾸려면 /SOLU 에서 요소번호 범위로 SFE 를 다시 걸어야
하는데, moa 실측에서 그 경로가 **최저온도 62.46 °C** 를 만들었다 — 유일한 디리클레가
오일 70 °C 이고 발열이 전부 양수이므로 최대원리상 불가능한 값이다(러너의 게이트가 잡았다).

그래서 세션 하나가 h 세트 하나만 담당하고(`--htc-set base` / `--htc-set sph`),
결과 JSON 두 개를 이 스크립트가 합친다. 설정 30 초를 한 번 더 쓰는 대신 결함 경로를
아예 지나가지 않는다.

계획서 규약: `runs` 는 64 엔트리(4 속도 × 4 전류 × 2 케이스 × 2 h 세트),
`I_cont_Arms` 는 {h 세트 → 케이스 → 속도문자열}.

사용법
------
    python merge_d1_hsets.py --base <e10_cont_rating_base.json> \
                             --sph  <e10_cont_rating_sph.json> \
                             --out  <e10_cont_rating.json>
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# h 세트별로 갈라지는 필드 = 두 파일의 서브딕트를 그대로 합친다
HSET_KEYED = (
    "I_cont_Arms", "I_cont_winding_Arms", "I_cont_magnet_Arms",
    "I_cont_limited_by", "I_cont_status", "I_cont_detail",
)
# 값이 h 세트마다 다르지만 키가 h 세트가 아닌 필드 = {hset: value} 로 감싼다
WRAP_PER_HSET = ("influence_coeffs", "_timing", "_run_dir", "_rth")


def load(path):
    if not os.path.isfile(path):
        sys.exit("missing input: %s" % path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description="merge D1 per-h-set outputs into one file")
    ap.add_argument("--base", required=True)
    ap.add_argument("--sph", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--json-indent", type=int, default=1)
    a = ap.parse_args()

    b, s_ = load(a.base), load(a.sph)

    for d, nm, want in ((b, "base", "base"), (s_, "sph", "sph")):
        got = sorted(d.get("I_cont_Arms", {}))
        if got != [want]:
            sys.exit("%s file holds h-sets %s, expected exactly ['%s']" % (nm, got, want))
        if d.get("_aborted"):
            sys.exit("%s run is marked _aborted=%r -- refusing to merge a failed run"
                     % (nm, d["_aborted"]))

    out = dict(b)  # 메타데이터는 base 쪽을 뼈대로 쓴다

    # 1) runs: 32 + 32 = 64, 계획서 순서(속도 -> 전류 -> 케이스 -> h세트)로 정렬
    runs = list(b["runs"]) + list(s_["runs"])
    case_rank = {"DC": 0, "AC": 1}
    hset_rank = {"base": 0, "sph": 1}
    runs.sort(key=lambda r: (float(r["speed"]), float(r["current"]),
                             case_rank.get(r["case"], 9), hset_rank.get(r["htc"], 9)))
    out["runs"] = runs

    # 2) h 세트로 키가 갈리는 필드
    for k in HSET_KEYED:
        if k in b or k in s_:
            merged = {}
            merged.update(b.get(k, {}))
            merged.update(s_.get(k, {}))
            out[k] = merged

    # 3) 세션마다 하나씩 나오는 필드는 h 세트로 감싼다
    for k in WRAP_PER_HSET:
        if k in b or k in s_:
            out[k] = {"base": b.get(k), "sph": s_.get(k)}

    # 3b) _superposition_check 는 소비자(make_thesis_figs.py)가 최상위 평면 dict 로 읽는다.
    #     h 세트별 상세는 per_hset 아래 보존하고, 요약은 두 세션 중 나쁜 쪽으로 합친다.
    bs, ss = b.get("_superposition_check") or {}, s_.get("_superposition_check") or {}
    def _worst(k):
        vals = [v for v in (bs.get(k), ss.get(k)) if isinstance(v, (int, float))]
        return max(vals) if vals else None
    both = [x for x in (bs.get("ok"), ss.get("ok")) if x is not None]
    out["_superposition_check"] = {
        "performed": bool(bs.get("performed")) and bool(ss.get("performed")),
        "ok": (all(both) if both else None),
        "tol_K": bs.get("tol_K", ss.get("tol_K")),
        "worst_err_K": _worst("worst_err_K"),
        "max_abs_err_K": _worst("max_abs_err_K"),
        "verified_htc_set": "base + sph (each verified in its own MAPDL session)",
        "per_hset": {"base": bs, "sph": ss},
    }

    # 3c) _undershoot 는 리스트다. out = dict(b) 로 base 것만 남으면 sph 기록이 사라진다.
    #     sph 세트는 냉각이 약해 구배가 급하므로 오히려 sph 쪽에 기록이 몰린다 -- 유실되면
    #     "관용된 언더슈트가 없었다" 는 거짓 기록이 된다.
    us = list(b.get("_undershoot") or []) + list(s_.get("_undershoot") or [])
    if us or ("_undershoot" in b) or ("_undershoot" in s_):
        out["_undershoot"] = us

    # 4) 합성 사실을 기록에 남긴다
    notes = list(out.get("_notes") or [])
    notes.append(
        "이 파일은 merge_d1_hsets.py 가 두 개의 단일 h 세트 실행을 합친 것이다. "
        "한 세션에서 h 세트를 바꾸면 SURF152 대류 재적용 경로가 최저온도 62.46 degC "
        "(오일 디리클레 70 degC 미만 = 최대원리 위반) 를 만들어, h 세트마다 별도 세션으로 돌렸다.")
    out["_notes"] = notes
    out["_merged_from"] = {
        "base": os.path.basename(a.base),
        "sph": os.path.basename(a.sph),
        "by": "merge_d1_hsets.py",
        "why": ("SURF152 convection is written once at ESURF time; re-issuing SFE in /SOLU "
                "for a second h-set produced a max-principle violation on moa."),
    }

    n_hsets = len(out.get("I_cont_Arms", {}))
    n_runs = len(runs)
    if n_runs != 64 or n_hsets != 2:
        print("[warn] merged file has %d runs and %d h-sets (plan expects 64 and 2)"
              % (n_runs, n_hsets))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=a.json_indent)
    print("wrote %s (%d runs, h-sets %s, %.1f KB)"
          % (a.out, n_runs, sorted(out.get("I_cont_Arms", {})),
             os.path.getsize(a.out) / 1024.0))
    for hs in sorted(out.get("I_cont_Arms", {})):
        for case in ("DC", "AC"):
            row = out["I_cont_Arms"][hs].get(case, {})
            vals = " ".join("%s:%s" % (k, ("%.1f" % v) if isinstance(v, (int, float)) else v)
                            for k, v in sorted(row.items(), key=lambda kv: int(kv[0])))
            print("  I_cont %-4s %-2s  %s" % (hs, case, vals))


if __name__ == "__main__":
    main()
