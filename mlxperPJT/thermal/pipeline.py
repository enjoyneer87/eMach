# -*- coding: utf-8 -*-
"""모터 열해석 자동화 파이프라인 — 단계 레지스트리 + 실행 CLI.

Motor-CAD → Maxwell → (gmsh 메시) → MAPDL 하이브리드 → FreeFlow 커플링 → Icepak/IcepakFEA
→ Fluent → Mechanical(구조) → 시각화 를 하나의 단계 목록으로 묶는다. 각 단계 스크립트는
기존 그대로(대부분 moa 경로 하드코딩) 두고, 이 파일은 순서·입출력·실행 방식만 정의한다.

    python pipeline.py list [--chain e10]        단계 목록
    python pipeline.py show e10.mapdl_hybrid     단계 상세(입출력·주의)
    python pipeline.py check e10                 입력 파일·파이썬 모듈 사전 점검 (체인 또는 단계)
    python pipeline.py init                      스크래치 폴더(C:\\work\\thermal_scratch) 준비
    python pipeline.py run e10.mapdl_hybrid      실행 (--detached: 백그라운드, --dry-run: 명령만)

표준 라이브러리만 사용(Python 3.10+). 결과는 한 줄 JSON 으로 출력한다(토큰 절약).
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

THERMAL = Path(__file__).resolve().parent
REPO = THERMAL.parents[1]
# 단계 스크립트들이 하드코딩한 위치. 다른 PC에서는 환경변수로 바꿔 check 만 맞출 수 있다
# (스크립트 자체 경로는 여전히 moa 기준 — README "이식성" 참조).
SIMVARY = Path(os.environ.get("THERMAL_SIMVARY", r"D:\KDH\simVary"))
SCRATCH = Path(os.environ.get("THERMAL_SCRATCH", r"C:\work\thermal_scratch"))
FFPROJ = SIMVARY / r"simFreeFlow\20251226\FreeFlow\FreeFlowProject"
ANSYS_ROOT = Path(os.environ.get("ANSYS_ROOT", r"C:\Program Files\ANSYS Inc\v261"))
FREEFLOW_EXE = ANSYS_ROOT / r"FreeFlow\bin\FreeFlow.exe"
SKILL_SCRIPTS = REPO / ".claude" / "skills" / "motor-thermal-hybrid" / "scripts"

TOOL_MODULES = {
    "Motor-CAD": ["ansys.motorcad.core"],
    "Maxwell": ["ansys.aedt.core"],
    "Icepak": ["ansys.aedt.core"],
    "IcepakFEA": ["ansys.aedt.core"],
    "gmsh": ["gmsh"],
    "MAPDL": ["ansys.mapdl.core"],
    "Mechanical": ["ansys.mapdl.reader"],
    "Fluent": ["ansys.fluent.core"],
    "FreeFlow": [],
    "viz": ["pyvista", "matplotlib"],
    "h5py": ["h5py"],
}


@dataclass
class Stage:
    id: str
    chain: str
    tool: str
    script: str                      # THERMAL 기준 상대경로 (또는 repo: 접두어)
    desc: str
    inputs: list = field(default_factory=list)
    outputs: list = field(default_factory=list)
    args: list = field(default_factory=list)
    env: dict = field(default_factory=dict)
    mode: str = "auto"               # auto | freeflow | gui | notebook | ps1
    after: list = field(default_factory=list)
    note: str = ""

    @property
    def path(self) -> Path:
        if self.script.startswith("repo:"):
            return REPO / self.script[5:]
        return THERMAL / self.script


def _p(s: str) -> str:
    return (s.replace("{SV}", str(SIMVARY)).replace("{FF}", str(FFPROJ))
             .replace("{T}", str(THERMAL)).replace("{SCRATCH}", str(SCRATCH))
             .replace("{REPO}", str(REPO)))


E10_MOT = "{SV}\\e10_6TSweep\\refModel\\e10Turn6V261.mot"
E10_CDB2 = "{SV}\\Ansys_Thermal\\ff_e10_mesh_v2.cdb"
E10_IPK = "{SV}\\Ansys_Thermal\\e10_icepak_hybrid.aedt"
PR_AEDT = "{SV}\\Ansys_Thermal\\SyC_Mxwl_Fluent_eMachine_2022r2\\Initial_ProjectFiles\\Prius_Model_24R2.aedt"
PR_STEP = "{SV}\\Ansys_Thermal\\Flu_MacTherm_EN_ILT_2019"
PR_CDB = "{SV}\\Ansys_Thermal\\prius_motor_mesh.cdb"
PR_CAS = PR_STEP + "\\FLU_EMTHERM_2019R2_2021R1_EN_M02-FluentSetup\\2019R2\\PriusMotor_3D45degree.cas.h5"
PR_IPK = "{SV}\\Ansys_Thermal\\Prius_work\\Prius_Icepak.aedt"
KIT = "plans/PLAN_20260906_assets"

STAGES = [
    # ───── e10 : FreeFlow 오일냉각 모터 (Motor-CAD → Maxwell → MAPDL ⇄ FreeFlow → Icepak) ─────
    Stage("e10.mcad_losses", "e10", "Motor-CAD", "freeflow/scripts/01_e10_motorcad_losses.py",
          "Motor-CAD .mot 운전점·손실 추출", [E10_MOT], ["{T}\\freeflow\\data\\e10_losses.json"],
          note="헤드리스에서 thermal injected loss 가 0 으로 나올 수 있음 → Magnetics 출력 사용(skill gotchas)."),
    Stage("e10.ff_geom", "e10", "viz", "freeflow/scripts/02_ff_dimensions.py",
          "FreeFlow STL 치수·극수 추출", ["{FF}\\Geometry"], ["{SCRATCH}\\ff_dims_out.txt"]),
    Stage("e10.maxwell_geom", "e10", "Maxwell", "freeflow/scripts/02c_maxwell_geom_extract.py",
          "Maxwell 2D 로터·더블V 자석·샤프트 단면 폴리곤 추출",
          ["{SV}\\e10_20251226\\e10_User_2D_GF0_RD1AS0AC1WG0HCT1HET0_ANSYSEM_2D.aedt"], ["{SCRATCH}"]),
    Stage("e10.mesh_stl", "e10", "gmsh", "freeflow/scripts/03_stl_to_cdb.py",
          "스테이터+권선 STL → tet10 CDB (병합 후 퇴화 필터)", ["{FF}\\Geometry"],
          ["{SV}\\Ansys_Thermal\\ff_e10_mesh.cdb"], after=["e10.ff_geom"]),
    Stage("e10.mesh_v2", "e10", "gmsh", "freeflow/scripts/03b_rotor_from_maxwell.py",
          "Maxwell 2D 로터·자석·샤프트 재구축 + 스테이터 병합 → v2 CDB (1.1M 절점)",
          ["{SV}\\Ansys_Thermal\\ff_e10_mesh.cdb"], [E10_CDB2], after=["e10.maxwell_geom", "e10.mesh_stl"],
          note="EBLOCK tet10 줄바꿈 규칙(11헤더+8노드/2노드). 260MB, git 밖."),
    Stage("e10.mapdl_hybrid", "e10", "MAPDL", "freeflow/scripts/04_mapdl_thermal.py",
          "JAC279 하이브리드: 3D FEM + 오일 열등가회로(JACKET/SPRAY/GAP/SHF) 과도 900s",
          [E10_CDB2, "{T}\\freeflow\\data\\e10_losses.json"],
          ["{T}\\freeflow\\data\\ff_mapdl_hybrid_temps.json", "{SCRATCH}\\ff_hybrid_v2_run2\\file.rth"],
          after=["e10.mesh_v2", "e10.mcad_losses"],
          note="기준값: 권선 152.2 / 스테이터 126.0 / 자석 86.9 °C. 솔브 ~13분. 먼저 ansys_clean."),
    Stage("e10.mapdl_viz", "e10", "viz", "freeflow/scripts/10_mapdl_dashboard_viz.py",
          "표준 시각화 세트 + 대시보드 GIF", ["{SCRATCH}\\ff_hybrid_v2_run2\\file.rth"],
          ["{T}\\freeflow\\viz\\mapdl"], after=["e10.mapdl_hybrid"],
          note="matplotlib 3.10 이면 회로 오버레이만 실패(cm.get_cmap)."),
    Stage("e10.ff_oil_viz", "e10", "h5py", "freeflow/scripts/06_oil_static_viz.py",
          "FreeFlow 오일 SPH 속도장 정적 그림", ["{FF}\\Project.freeflow.files\\simulation"], ["{SCRATCH}\\ff_oil"]),
    Stage("e10.ff_thermal_setup", "e10", "FreeFlow", "freeflow/scripts/11_freeflow_thermal_setup.py",
          "열모델 ON + MAPDL 벽온도 4개 + ATF 물성 → Project_thermal 저장",
          ["{FF}\\Project.freeflow", "{T}\\freeflow\\data\\ff_mapdl_hybrid_temps.json"],
          ["{FF}\\Project_thermal.freeflow"], mode="freeflow", after=["e10.mapdl_hybrid"],
          note="원본 Project.freeflow 덮어쓰기 금지. 물리설정 변경 시 결과셋 전체 무효."),
    Stage("e10.ff_thermal_solve", "e10", "FreeFlow", "freeflow/scripts/12_freeflow_thermal_solve.py",
          "Inlet 70°C + 밀도 교정 + 1-way 열 솔브 (GPU)", ["{FF}\\Project_thermal.freeflow"],
          ["{FF}\\Project_thermal.freeflow.files"], mode="freeflow", after=["e10.ff_thermal_setup"],
          note="Fluid Inlet 기본 0°C 함정. 8s 전체는 GPU 수 시간 → --detached 필수."),
    Stage("e10.ff_thermal_viz", "e10", "h5py", "freeflow/scripts/13_freeflow_thermal_viz.py",
          "오일 온도장 그림 + 이력", ["{FF}\\Project_thermal.freeflow.files\\simulation"],
          ["{T}\\freeflow\\viz\\freeflow"], after=["e10.ff_thermal_solve"]),
    Stage("e10.icepak_v1_steady", "e10", "Icepak", "icepak_e10/scripts/10_v1_homog_htc_steady.py",
          "Icepak V1: 네이티브 카브 균질 권선 + 대류벽(MAPDL 오일노드 ref) 정상", [E10_IPK], [E10_IPK],
          after=["e10.mapdl_hybrid"], note="Network 경계 금지·Region 제거(skill gotchas)."),
    Stage("e10.icepak_v1_trans", "e10", "Icepak", "icepak_e10/scripts/11_v1_homog_transient.py",
          "Icepak V1 과도 900s — MAPDL 과 동일 조건", [E10_IPK],
          ["{T}\\freeflow\\data\\e10_icepak_v1_homog.json"], after=["e10.icepak_v1_steady"],
          note="기준값: 권선 136.5 °C (MAPDL 대비 10% 이내)."),
    Stage("e10.icepak_v2_bars", "e10", "Icepak", "icepak_e10/scripts/12_v2_discrete_bars_clip.py",
          "Icepak V2: Maxwell 3D 하이핀 바 import (비컨포멀 실패 사례 재현용)",
          [E10_IPK, "{SV}\\e10_6TSweep\\refModel\\e10Turn6V261_3D_Script_ANSYSEM_3D.aedt"], [E10_IPK],
          note="결과는 비물리(2376°C) — '실패 자체가 결과'."),
    Stage("e10.compare", "e10", "viz", "freeflow/scripts/19_e10_mapdl_icepak_compare.py",
          "MAPDL vs Icepak 비교 차트", ["{T}\\freeflow\\data"], ["{T}\\freeflow\\viz\\comparison"],
          after=["e10.mapdl_hybrid", "e10.icepak_v1_trans"]),

    # ───── prius : 실제 Toyota Prius (Maxwell → MAPDL ↔ Fluent ↔ Icepak 교차검증) ─────
    Stage("prius.maxwell_losses", "prius", "Maxwell", "prius/scripts/01_maxwell_extract_losses.py",
          "Maxwell 2D 과도 손실 추출(슬롯·엔드 동손, 철손, 자석)", [PR_AEDT],
          ["{SV}\\Ansys_Thermal\\prius_losses.json"],
          note="19R2 원본은 24R2 재저장본 사용. 철손 분리는 90/10 추정."),
    Stage("prius.mesh", "prius", "gmsh", "prius/scripts/02_step_to_cdb.py",
          "STEP → 활성부 분류 → 컨포멀 tet10 → 45°×8 → CDB", [PR_STEP], [PR_CDB]),
    Stage("prius.mapdl_jac279", "prius", "MAPDL", "prius/scripts/03_mapdl_thermal.py",
          "MAPDL 하이브리드(JAC279 회로 냉각) 과도", [PR_CDB, "{SV}\\Ansys_Thermal\\prius_losses.json"],
          ["{SCRATCH}"], after=["prius.mesh", "prius.maxwell_losses"],
          note="냉각 조건이 Fluent 와 달라 직접 비교 불가(코일 185.6 °C)."),
    Stage("prius.mapdl_wj_low", "prius", "MAPDL", "prius/scripts/08_mapdl_waterjacket.py",
          "Fluent 조건 정합(워터재킷) 저부하 — 교차검증용", [PR_CDB], ["{SCRATCH}"],
          env={"PRIUS_LOAD": "low"}, after=["prius.mesh"], note="기준값: 코일 88.3 °C (Fluent 88.3)."),
    Stage("prius.mapdl_wj_high", "prius", "MAPDL", "prius/scripts/08_mapdl_waterjacket.py",
          "Fluent 조건 정합(워터재킷) 250A", [PR_CDB], ["{SCRATCH}"],
          env={"PRIUS_LOAD": "high"}, after=["prius.mesh"], note="기준값: 코일 119.2 °C (Fluent 118.2)."),
    Stage("prius.fluent_extract", "prius", "h5py", "prius/scripts/05_fluent_extract_zone_temps.py",
          "Fluent .cas/.dat.h5 → 존별 온도 (라이선스 불요)", [PR_CAS],
          ["{SV}\\Ansys_Thermal\\fluent_prius_zone_temps.json"]),
    Stage("prius.fluent_250A", "prius", "Fluent", "prius/scripts/09_fluent_250A_resolve.py",
          "Fluent 소스항 250A 교체 후 CHT 재솔브", [PR_CAS],
          ["{SV}\\Ansys_Thermal\\fluent_prius_250A_zone_temps.json"]),
    Stage("prius.validation", "prius", "viz", "prius/scripts/10_validation_matrix.py",
          "MAPDL vs Fluent 검증 매트릭스 차트", [], ["{T}\\prius\\viz\\comparison"],
          after=["prius.mapdl_wj_low", "prius.mapdl_wj_high", "prius.fluent_250A"]),
    Stage("prius.viz", "prius", "viz", "prius/scripts/render_prius_viz.py", "워터재킷 저/고부하 표준 시각화 일괄",
          ["{SCRATCH}"], ["{T}\\prius\\viz"], args=["all"], after=["prius.mapdl_wj_low", "prius.mapdl_wj_high"]),
    Stage("prius.icepak_import", "prius", "Icepak", "prius/icepak/01_import_classify_materials.py",
          "Icepak: STEP 임포트·bbox 분류·재료", [PR_STEP], [PR_IPK]),
    Stage("prius.icepak_sources", "prius", "Icepak", "prius/icepak/02_materials_sources.py",
          "이방성 코일 재료 + 손실 블록", [PR_IPK], [PR_IPK], after=["prius.icepak_import"]),
    Stage("prius.icepak_solve", "prius", "Icepak", "prius/icepak/05_fixedT_solve_extract.py",
          "프레임 OD 고정온도 솔브·추출 (HTC 벽 단락 회피)", [PR_IPK],
          ["{T}\\prius\\data\\icepak_prius_250A_temps.json"], after=["prius.icepak_sources"],
          note="고정온도 우회라 계통적 고온(코일 176 °C) — 정성 비교용."),
    Stage("prius.threeway", "prius", "viz", "prius/icepak/07_threeway_compare.py", "Fluent/MAPDL/Icepak 3-way 차트",
          ["{T}\\prius\\data\\icepak_prius_250A_temps.json"], ["{T}\\prius\\viz\\comparison"],
          after=["prius.icepak_solve", "prius.validation"]),

    # ───── mech : AEDT Mechanical(IcepakFEA) 열 / Mechanical 구조 / NVH 가진력 ─────
    Stage("mech.aedt_thermal_build", "mech", "IcepakFEA", "WS01_2_AEDT_Mechanical_Thermal_build.ipynb",
          "Maxwell → AEDT Mechanical Thermal 모델 빌드(duplicate·재질·대류·회전유체·접촉·EM손실)",
          mode="notebook", note="전제: Maxwell 'Create Target Design' 수동 완료. 대류는 고정 HTC 경계."),
    Stage("mech.c67_stress", "mech", "Mechanical", f"{KIT}/d6_c67_stress.py",
          "Mechanical rst → 회전자 원심 응력·변위 + 속도 스윕", args=["--repo", "{REPO}"],
          outputs=["{T}\\thesis_out\\c67_stress.json"],
          note="plans/ 는 학위논문 세션 관할(읽기전용). ds.dat 재솔브 시 OMEGA 이중적용 주의."),
    Stage("mech.em2struct", "mech", "Mechanical", "repo:tools/em2struct/examples/example_airgap_to_structural.py",
          "전자계 가진력 → 구조 메시 보존 맵핑(Mechanical/LS-DYNA/Motion) — NVH 1-way",
          note="패키지 사용법은 tools/em2struct/README.md."),

    # ───── fluent : 엔드턴 오일 스프레이 CHT ─────
    Stage("fluent.spray_geom", "fluent", "gmsh", "fluent_spray/geometry/build_spray_chamber.py",
          "스프레이 캐비티 형상(STL, 명명경계) 생성", [], ["{T}\\fluent_spray\\geometry"]),
    Stage("fluent.spray_mesh", "fluent", "Fluent", "fluent_spray/README_fluent_spray.md",
          "Fluent Meshing watertight 볼륨메시", mode="gui", after=["fluent.spray_geom"],
          note="헤드리스 변환 6종 실패 — GUI 필수(README 순서)."),
    Stage("fluent.spray_cht", "fluent", "Fluent", "fluent_spray/oil_spray_cht_recipe.py",
          "DPM 스프레이 + EWF + 고체 발열원 CHT 셋업·솔브", args=["<case_or_mesh.h5>"],
          after=["fluent.spray_mesh"]),

    # ───── thesis : 학위논문 킷 D1~D6 (plans/, 읽기전용 참조 구현) ─────
    Stage("thesis.preflight", "thesis", "MAPDL", f"{KIT}/preflight.py", "환경·CDB·라이선스 사전점검",
          [E10_CDB2], args=["--repo", "{REPO}", "--cdb", E10_CDB2, "--deep"]),
    Stage("thesis.d1", "thesis", "MAPDL", f"{KIT}/d1_cont_rating.py", "연속 정격 곡선(중첩법)",
          [E10_CDB2], ["{T}\\thesis_out\\e10_cont_rating.json"],
          args=["--repo", "{REPO}", "--cdb", E10_CDB2, "--mode", "super", "--htc-set", "both"],
          after=["thesis.preflight"], note="정상해석 1런 54s. 다중 하중단계 BC 재지정 규칙."),
    Stage("thesis.d2", "thesis", "MAPDL", f"{KIT}/d2_ac_turnwise.py", "턴별 AC 손실 주입 vs 균일",
          [E10_CDB2], ["{T}\\thesis_out\\e10_ac_turnwise_hotspot.json"],
          args=["--repo", "{REPO}", "--cdb", E10_CDB2], after=["thesis.preflight"]),
    Stage("thesis.d3", "thesis", "h5py", f"{KIT}/d3_htc_backout.py", "FreeFlow SPH 결과로 HTC 역산",
          ["{FF}\\Project.freeflow.files\\simulation"], ["{T}\\thesis_out\\htc_backout_horizontal.json"],
          args=["--repo", "{REPO}"]),
    Stage("thesis.d4", "thesis", "Motor-CAD", f"{KIT}/run_d4_interactive.ps1",
          "Motor-CAD 전류·속도 의존 손실 맵 (대화형 세션 예약실행)", [E10_MOT], mode="ps1",
          note="사용자가 연 Motor-CAD 에 attach 금지. 손실 0 + PASS 는 무효."),
    Stage("thesis.figs", "thesis", "viz", f"{KIT}/make_thesis_figs.py", "논문 그림 일괄",
          args=["--repo", "{REPO}"], after=["thesis.d1", "thesis.d2", "thesis.d3"]),
]
BY_ID = {s.id: s for s in STAGES}
CHAINS = sorted({s.chain for s in STAGES})


def _emit(obj):
    print(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def _select(target):
    if target in BY_ID:
        return [BY_ID[target]]
    if target in CHAINS:
        return [s for s in STAGES if s.chain == target]
    if target == "all":
        return list(STAGES)
    raise SystemExit(f"unknown stage/chain: {target} (chains: {', '.join(CHAINS)})")


def cmd_list(a):
    rows = [s for s in STAGES if not a.chain or s.chain == a.chain]
    w = max(len(s.id) for s in rows)
    for s in rows:
        print(f"{s.id:<{w}}  {s.tool:<10} {s.mode:<8} {s.desc}")


def cmd_show(a):
    s = BY_ID.get(a.stage) or sys.exit(f"unknown stage: {a.stage}")
    _emit({"id": s.id, "tool": s.tool, "mode": s.mode, "script": str(s.path),
           "args": [_p(x) for x in s.args], "env": s.env, "after": s.after,
           "inputs": [_p(x) for x in s.inputs], "outputs": [_p(x) for x in s.outputs],
           "desc": s.desc, "note": s.note})


def _check_stage(s):
    missing = [_p(x) for x in s.inputs if not Path(_p(x)).exists()]
    mods = [m for m in TOOL_MODULES.get(s.tool, []) if _safe_spec(m) is None]
    r = {"id": s.id, "script_ok": s.path.exists(), "missing_inputs": missing, "missing_modules": mods}
    if s.mode == "freeflow":
        r["freeflow_exe"] = FREEFLOW_EXE.exists()
    r["ok"] = r["script_ok"] and not missing and not mods and r.get("freeflow_exe", True)
    return r


def _safe_spec(name):
    try:
        return importlib.util.find_spec(name)
    except (ImportError, ValueError):
        return None


def cmd_check(a):
    res = [_check_stage(s) for s in _select(a.target)]
    _emit({"ok": sum(r["ok"] for r in res), "total": len(res),
           "problems": [r for r in res if not r["ok"]]})


SCRATCH_DIR_RE = re.compile(r"thermal_scratch\\([A-Za-z0-9_.\-]+)")
JOIN_RE = re.compile(r"join\(\s*(?:SP|OSP|NSP|RTH_ROOT)\s*,\s*[\"']([A-Za-z0-9_.\-]+)[\"']")
FILE_EXT = re.compile(r"\.(txt|json|png|gif|csv|log|stl|h5|cdb|rth|py|msh|freeflow)$", re.I)


def cmd_init(a):
    """스크립트들이 여는 스크래치 하위 폴더를 미리 만든다(대부분 makedirs 없이 open 함)."""
    dirs = set()
    for p in list(THERMAL.rglob("*.py")):
        if "plans" in p.parts:
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        dirs.update(m for m in SCRATCH_DIR_RE.findall(txt) + JOIN_RE.findall(txt) if not FILE_EXT.search(m))
    SCRATCH.mkdir(parents=True, exist_ok=True)
    for d in sorted(dirs):
        (SCRATCH / d).mkdir(parents=True, exist_ok=True)
    _emit({"scratch": str(SCRATCH), "subdirs": sorted(dirs)})


def _command(s, python):
    args = [_p(x) for x in s.args]
    if s.mode == "freeflow":
        return [str(FREEFLOW_EXE), "--headless", "--script", str(s.path)] + args
    if s.mode == "ps1":
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(s.path)] + args
    return [python, "-X", "utf8", str(s.path)] + args


def cmd_run(a):
    s = BY_ID.get(a.stage) or sys.exit(f"unknown stage: {a.stage}")
    if s.mode in ("gui", "notebook"):
        _emit({"id": s.id, "status": "manual", "how": f"{s.mode}: {s.path}", "note": s.note})
        return
    chk = _check_stage(s)
    if not chk["ok"] and not a.force:
        _emit({"id": s.id, "status": "blocked", "check": chk, "hint": "--force 로 무시 가능"})
        sys.exit(2)
    cmd = _command(s, a.python)
    env = dict(os.environ, PYTHONUTF8="1", **s.env)
    if a.dry_run:
        _emit({"id": s.id, "cmd": cmd, "env": s.env, "cwd": str(s.path.parent)})
        return
    if a.detached:
        runner = SKILL_SCRIPTS / "run_detached.ps1"
        if s.mode != "auto" or not runner.exists():
            sys.exit("--detached 는 python 단계 + .claude/skills/motor-thermal-hybrid/scripts 가 필요")
        ps = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(runner),
              "-Script", str(s.path), "-Name", s.id.replace(".", "_"), "-Python", a.python]
        if s.args:
            ps += ["-ScriptArgs"] + [_p(x) for x in s.args]
        if a.scheduled_task:
            ps.append("-ScheduledTask")
        out = subprocess.run(ps, capture_output=True, text=True, env=env)
        _emit({"id": s.id, "launched": out.returncode == 0, "out": out.stdout.strip()[-300:],
               "err": out.stderr.strip()[-300:],
               "next": "wait_done.ps1 -RunDir <RUN_DIR> 를 백그라운드로 한 번 실행"})
        return
    r = subprocess.run(cmd, cwd=str(s.path.parent), env=env)
    _emit({"id": s.id, "exit_code": r.returncode, "outputs": [_p(x) for x in s.outputs]})
    sys.exit(r.returncode)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--chain", choices=CHAINS); p.set_defaults(f=cmd_list)
    p = sub.add_parser("show"); p.add_argument("stage"); p.set_defaults(f=cmd_show)
    p = sub.add_parser("check"); p.add_argument("target", nargs="?", default="all"); p.set_defaults(f=cmd_check)
    p = sub.add_parser("init"); p.set_defaults(f=cmd_init)
    p = sub.add_parser("run"); p.add_argument("stage")
    p.add_argument("--python", default=sys.executable)
    p.add_argument("--detached", action="store_true"); p.add_argument("--scheduled-task", action="store_true")
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--force", action="store_true")
    p.set_defaults(f=cmd_run)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
