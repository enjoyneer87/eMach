# -*- coding: utf-8 -*-
"""Section 5.4 check: the compute cost of the two-model study, measured.

Section 5.4 reports 11.3 h against 38.0 h of exhaustive Full-FEA, about
70 % less.  Those are measurements, not a rate assumption, and this check
reproduces them from what the solver left behind.

Three sources, all outside the manuscript:

``MessageLogs/messageLog_*.txt``
    Motor-CAD stamps every line with a wall clock time, so a build's
    elapsed time is the span of its own log, and "FEA Calculation Time:
    N Seconds" gives solver-only time per solve.  The 30-point MS-FEA
    saturation sweep is measured this way.
``ACLossCalcExport_<scale>_no_txt/<mode>_Speed_*RPM_*A_*deg/``
    one directory per operating point; the span of the file mtimes inside
    it is that point's solve time.  Per-point time is strongly speed
    dependent, which is the whole reason a flat rate misstates the
    anchor-heavy calibration plans.
``_txt_backfill/<scale>/*/FEA_data.txt.gz``
    the field export, and the element/node counts that explain why SC
    costs more per point than Ref.

The exports and logs are raw Motor-CAD artefacts and are not deposited,
so ``--recompute`` needs a local analysis tree and exits 2 without one,
as ``check_field_similarity`` does.  The shipped JSON carries the
aggregate the manuscript and Fig. 12 both quote.

Exit codes: 0 pass / 1 tolerance exceeded or missing shipped JSON /
2 raw inputs unavailable for --recompute.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import re
import statistics
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
for _cand in (os.path.abspath(os.path.join(HERE, "..", "..", "tools")),
              os.path.abspath(os.path.join(HERE, ".."))):
    if os.path.isdir(os.path.join(_cand, "jeet_acloss_rbf")) \
            and _cand not in sys.path:
        sys.path.insert(0, _cand)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from jeet_acloss_rbf import repro_env                       # noqa: E402

# 원자료 뿌리. 배포본에는 없다 — JEET_MCAD_ROOT (또는 다른 검증
# 스크립트와 공통인 JEET_FEA_ROOT) 로 지정한다. 기본값은 두지 않는다:
# 저자 기계의 경로가 배포본에 남으면 안 되고, 미설정은 exit 2 여야 한다.
MCAD_ROOT = (os.environ.get("JEET_MCAD_ROOT")
             or os.environ.get("JEET_FEA_ROOT") or "")

# 채택 플랜 (AF_model_<scale>_exponent.json 의 _meta.plan, Table 2 와 대조)
#   Ref  24 @16k + 4 @ 2/4/8k = 36 Full-FEA
#   SC   24 @16k + 3 @ 8k     = 27 Full-FEA
PLAN = {"Ref": [(16000, 24), (2000, 4), (4000, 4), (8000, 4)],
        "SC": [(16000, 24), (8000, 3)]}
VERIFY_SPEEDS = (2000, 4000, 8000, 16000)
VERIFY_PER_SPEED = 30           # 5 전류 x 6 위상각

# Table 2 가 Full-FEA 로 세지 않는, 저속 슬롯 B 입력용 MS-FEA 포화 스윕
SAT_LOG = {
    "Ref": os.path.join("refModel", "e10Turn6V261_Lab30", "MessageLogs",
                        "messageLog_22376.txt"),
    "SC": os.path.join("SLFEA", "e10Turn6V261SLFEA_Lab30", "MessageLogs",
                       "messageLog_28928.txt"),
}

EXPORT_ROOT = {"Ref": "ACLossCalcExport_Ref_no_txt",
               "SC": "ACLossCalcExport_SC_no_txt"}
# 저자 분류(2026-08-21): 와전류가 없는 시간이산 해석은 TS MS-FEA 다.
MODE_LABEL = {"Hybrid": "ts_msfea", "FullFEA": "ts_fullfea"}

PT = re.compile(r"^(?P<mode>\w+?)_Speed_(?P<spd>\d+)RPM_(?P<amp>[\d.]+)A_"
                r"(?P<beta>[\d.]+)deg$")
STAMP = re.compile(r"^(\d{2}/\d{2}/\d{4} \d{1,2}:\d{2}:\d{2} [AP]M)\s*:")
TABLE = re.compile(r"^\s*(\d+)\s+(\d+)\s+(ElementsTable|NodesTable)")


def _log_span_h(path):
    """Elapsed hours spanned by a Motor-CAD message log."""
    stamps = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = STAMP.match(line.strip())
            if m:
                stamps.append(datetime.strptime(m.group(1),
                                                "%d/%m/%Y %I:%M:%S %p"))
    if len(stamps) < 2:
        return None
    return (max(stamps) - min(stamps)).total_seconds() / 3600.0


def _point_seconds(d):
    """Elapsed seconds of one operating point, from its file mtimes."""
    ts = []
    for dp, _dirs, files in os.walk(d):
        for f in files:
            try:
                ts.append(os.path.getmtime(os.path.join(dp, f)))
            except OSError:
                pass
    return (max(ts) - min(ts)) if len(ts) >= 2 else None


def _mesh_size(scale):
    """Element and node count from the first deposited field export."""
    pat = os.path.join(MCAD_ROOT, "_txt_backfill", scale, "*",
                       "FEA_data.txt.gz")
    files = sorted(glob.glob(pat))
    if not files:
        return {}
    out = {}
    with gzip.open(files[0], "rt", encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            m = TABLE.match(line)
            if m:
                out[m.group(3)] = int(m.group(2))
            if len(out) == 2 or i > 400000:
                break
    return {"elements": out.get("ElementsTable"),
            "nodes": out.get("NodesTable"),
            "source": os.path.basename(os.path.dirname(files[0]))}


def _unavailable():
    print("[raw inputs unavailable] %s\n  The Motor-CAD analysis tree "
          "is not part of the deposit. Set JEET_MCAD_ROOT to a local "
          "copy, or read the shipped JSON."
          % (MCAD_ROOT or "(JEET_MCAD_ROOT unset)"))
    return None


def recompute():
    if not MCAD_ROOT or not os.path.isdir(MCAD_ROOT):
        return _unavailable()

    res = {"per_point_seconds": {}, "mesh": {}, "saturation_sweep_h": {}}

    for scale, sub in EXPORT_ROOT.items():
        root = os.path.join(MCAD_ROOT, sub)
        if not os.path.isdir(root):
            continue
        # 속도별로 모으되, 검증 스윕과 같은 5 전류 격자로 제한한다.
        # Ref 16 kRPM 에는 저전류 3 단이 더 있어 섞으면 중앙값이 60 % 뛴다.
        buckets, amps = {}, {}
        for name in os.listdir(root):
            m = PT.match(name)
            if not m:
                continue
            sec = _point_seconds(os.path.join(root, name))
            if sec is None:
                continue
            key = (MODE_LABEL.get(m.group("mode"), m.group("mode")),
                   int(m.group("spd")))
            buckets.setdefault(key, []).append((float(m.group("amp")), sec))
            amps.setdefault(key, set()).add(float(m.group("amp")))
        base = {mode: amps.get((mode, 2000), set())
                for mode in set(k[0] for k in buckets)}
        for (mode, spd), rows in sorted(buckets.items()):
            keep = [s for a, s in rows if not base[mode] or a in base[mode]]
            if not keep:
                continue
            res["per_point_seconds"].setdefault(scale, {}).setdefault(
                mode, {})[str(spd)] = round(statistics.median(keep), 1)
        res["mesh"][scale] = _mesh_size(scale)

    for scale, rel in SAT_LOG.items():
        p = os.path.join(MCAD_ROOT, rel)
        if os.path.isfile(p):
            h = _log_span_h(p)
            if h is not None:
                res["saturation_sweep_h"][scale] = round(h, 3)

    res["_meta"] = {
        "plan": {k: v for k, v in PLAN.items()},
        "verify_points_per_model": len(VERIFY_SPEEDS) * VERIFY_PER_SPEED,
        "method": "per-point time = span of the file mtimes in that "
                  "operating point's export directory; restricted to the "
                  "5-current grid of the verification sweep. Saturation "
                  "sweep = span of its Motor-CAD message log.",
        "classification": "Hybrid_* exports are time-stepping solves "
                          "without conductor eddy currents, so they are "
                          "TS MS-FEA (author, 2026-08-21).",
        "excluded": "field export for the hybrid evaluation, 0.33 h over "
                    "30 points, is solver-specific overhead (39 s/point to "
                    "reopen the binary vs 2.7 s to read the text deposit) "
                    "and is not charged to the method.",
    }
    # 뿌리는 있는데 export 를 하나도 못 찾은 경우 — 빈 결과를
    # 돌려주면 호출부가 그것으로 동봉 JSON 을 덮어쓴다.
    if not any(v.get("ts_fullfea") for v in
               res["per_point_seconds"].values()):
        return _unavailable()
    return res


def _totals(res):
    pps = res.get("per_point_seconds", {})
    sat = res.get("saturation_sweep_h", {})
    base, calib = {}, {}
    for scale in ("Ref", "SC"):
        ff = pps.get(scale, {}).get("ts_fullfea", {})
        if not ff:
            continue
        base[scale] = sum(VERIFY_PER_SPEED * ff[str(s)]
                          for s in VERIFY_SPEEDS if str(s) in ff) / 3600.0
        calib[scale] = sum(n * ff[str(s)] for s, n in PLAN[scale]
                           if str(s) in ff) / 3600.0
    proposed = sum(calib.values()) + sat.get("Ref", 0.0)
    baseline = sum(base.values())
    return base, calib, proposed, baseline


def judge(res, tol_h, tol_pct):
    base, calib, proposed, baseline = _totals(res)
    if not base or not calib:
        print("[incomplete] the JSON carries no per-point Full-FEA times")
        return 1

    print("  per-point Full-FEA [s], on the verification sweep's "
          "5-current grid")
    for scale in ("Ref", "SC"):
        ff = res["per_point_seconds"].get(scale, {}).get("ts_fullfea", {})
        print("    %-4s " % scale + "  ".join(
            "%s rpm %5.0f" % (s, ff[str(s)])
            for s in VERIFY_SPEEDS if str(s) in ff))
    for scale, m in sorted(res.get("mesh", {}).items()):
        if m.get("elements"):
            print("    %-4s mesh %6d elements, %6d nodes"
                  % (scale, m["elements"], m["nodes"]))

    print("  exhaustive baseline  %5.2f h  (Ref %.2f + SC %.2f, "
          "%d points each)"
          % (baseline, base.get("Ref", 0), base.get("SC", 0),
             len(VERIFY_SPEEDS) * VERIFY_PER_SPEED))
    print("  proposed             %5.2f h  (sat sweep %.2f + Ref %.2f "
          "+ SC %.2f)"
          % (proposed, res.get("saturation_sweep_h", {}).get("Ref", 0),
             calib.get("Ref", 0), calib.get("SC", 0)))
    saving = 100.0 * (1.0 - proposed / baseline) if baseline else 0.0
    print("  saving               %5.1f %%" % saving)

    ok = True
    for name, got, want in (("baseline", baseline, 38.0),
                            ("proposed", proposed, 11.3)):
        if abs(got - want) > tol_h:
            print("  [FAIL] %s %.2f h differs from the manuscript's %.1f h "
                  "by more than %.2f h" % (name, got, want, tol_h))
            ok = False
    if abs(saving - 70.0) > tol_pct:
        print("  [FAIL] saving %.1f %% differs from the manuscript's 70 %% "
              "by more than %.1f pp" % (saving, tol_pct))
        ok = False
    print("  ->", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--recompute", action="store_true",
                    help="re-measure from the Motor-CAD logs and export "
                         "directories instead of reading the shipped JSON")
    ap.add_argument("--out", default=os.path.join(
        repro_env.checks_dir(), "compute_cost.json"))
    ap.add_argument("--tol-h", type=float, default=0.6,
                    help="allowed hour difference from the reported totals")
    ap.add_argument("--tol-pct", type=float, default=1.5,
                    help="allowed percentage-point difference in the saving")
    a = ap.parse_args()

    print("Check (Sec. 5.4): measured compute cost of the two-model study")
    if a.recompute:
        res = recompute()
        if res is None:
            return 2
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(res, fh, indent=1)
        print("saved:", a.out)
    else:
        if not os.path.isfile(a.out):
            print("[missing input] %s\n  Run with --recompute (a local "
                  "Motor-CAD analysis tree required), or restore the "
                  "shipped checks/ JSON." % a.out)
            return 1
        res = json.load(open(a.out, encoding="utf-8"))
    return judge(res, a.tol_h, a.tol_pct)


if __name__ == "__main__":
    raise SystemExit(main())
