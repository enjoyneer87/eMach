"""
pyMotorGeo.cli
==============

Command-line interface for motor geometry analysis without programming.

Provides easy access to pyMotorGeo analysis through shell commands, suitable for:
- Batch processing of multiple DXF files
- Integration into design workflows (CAD → scripts → FEA)
- Validation of motor CAD geometry
- Quick analysis without writing Python code

**Basic Commands**:

```bash
# Analyze motor and print summary
python -m pyMotorGeo analyze motor.dxf

# Specify pole/slot count (if automatic detection fails)
python -m pyMotorGeo analyze motor.dxf --poles 8 --slots 48

# Export results as JSON
python -m pyMotorGeo analyze motor.dxf --export json --output result.json

# Export as Pyleecan Machine (for FEA simulation)
python -m pyMotorGeo analyze motor.dxf --export pyleecan --output machine.pkl

# Export reconstructed motor as DXF
python -m pyMotorGeo analyze motor.dxf --export dxf --output motor_analyzed.dxf

# Print detailed debug information
python -m pyMotorGeo analyze motor.dxf --verbose

# Quick summary (fast, minimal output)
python -m pyMotorGeo quick motor.dxf
```

**Common Options**:

- `--poles N`: Override automatic pole count detection
- `--slots N`: Override automatic slot count detection
- `--rotor-topo {SPM|IPM|SynRM}`: Specify rotor topology type
- `--origin X,Y`: Set motor center coordinate (default: 0,0)
- `--export {json|dxf|pyleecan|summary}`: Output format
- `--output PATH`: Save results to file
- `--verbose`: Print detailed progress and debug info

**Exit Codes**:

- 0: Successful analysis
- 1: File not found or invalid DXF
- 2: Analysis error (missing parameters, invalid geometry)
- 3: Dependency error (missing library, e.g., pyleecan)

**Examples**:

Example 1: Batch process multiple motors

```bash
for file in *.dxf; do
    python -m pyMotorGeo analyze "$file" --export json --output "${file%.dxf}.json"
done
```

Example 2: Analyze and immediately export to Pyleecan for FEA

```bash
python -m pyMotorGeo analyze motor.dxf --rotor-topo IPMSM --export pyleecan --output motor_ipmsm.pkl
# Then in Python: import pickle; machine = pickle.load(open('motor_ipmsm.pkl'))
```

Example 3: Quick validation before detailed CAD review

```bash
python -m pyMotorGeo quick motor.dxf --verbose  # ~100ms
# If valid: proceed to detailed FEA; if invalid: redesign
```
"""
python -m pyMotorGeo info motor.dxf

# 버전 확인
python -m pyMotorGeo version
"""

import argparse
import sys
import os


def _print_face_table(faces, label: str) -> None:
    """face 리스트를 테이블 형태로 출력."""
    from region_closing import REGION_NAMES
    if not faces:
        return
    print(f"\n  {label} 영역 ({len(faces)}개):")
    print(f"  {'#':>3}  {'이름':<18}  {'area(mm²)':>10}  {'r_min':>7}  {'r_max':>7}")
    print(f"  {'─'*3}  {'─'*18}  {'─'*10}  {'─'*7}  {'─'*7}")
    for i, f in enumerate(faces):
        name_key = f.get('name', 'unknown')
        name_str = REGION_NAMES.get(name_key, name_key)
        area     = f.get('area', 0.0)
        r_min    = f.get('r_min', 0.0)
        r_max    = f.get('r_max', 0.0)
        print(f"  {i:>3}  {name_str:<18}  {area:>10.2f}  {r_min:>7.3f}  {r_max:>7.3f}")


def cmd_analyze(args) -> int:
    """analyze 명령어 핸들러."""
    dxf_path = args.dxf_file

    if not os.path.isfile(dxf_path):
        print(f"[오류] 파일을 찾을 수 없습니다: {dxf_path}", file=sys.stderr)
        return 1

    origin = (args.origin[0], args.origin[1]) if args.origin else (0.0, 0.0)

    from pipeline import analyze_dxf_v2, export_result_json

    result = analyze_dxf_v2(
        dxf_path,
        origin=origin,
        n_poles=args.poles,
        n_slots=args.slots,
        enable_radius_fallback=args.enable_radius_fallback,
        fallback_r_shaft_mm=args.fallback_shaft,
        fallback_r_stator_outer_mm=args.fallback_stator_outer,
        verbose=not args.quiet,
    )

    # face 테이블 출력
    if not args.quiet:
        _print_face_table(result.get('rotor_faces', []),  'Rotor')
        _print_face_table(result.get('stator_faces', []), 'Stator')
        print()

    # 내보내기
    if args.export == 'json':
        out = args.output or (os.path.splitext(dxf_path)[0] + '_result.json')
        export_result_json(result, out)

    elif args.export == 'pyleecan':
        out = args.output or (os.path.splitext(dxf_path)[0] + '_machine.json')
        _export_pyleecan(result, out)

    return 0


def _export_pyleecan(result: dict, output_path: str) -> None:
    """pyleecan Machine 객체를 JSON으로 저장."""
    from pyleecan_bridge import check_pyleecan_available, create_pyleecan_machine

    if not check_pyleecan_available():
        print("[경고] pyleecan이 설치되지 않았습니다. JSON 치수 파일로 대체합니다.",
              file=sys.stderr)
        from pipeline import export_result_json
        export_result_json(result, output_path)
        return

    dims = result.get('dims', {})
    machine = create_pyleecan_machine(dims)
    if machine is None:
        print("[경고] pyleecan Machine 객체 생성 실패.", file=sys.stderr)
        return

    machine.save(output_path)
    print(f"[export] pyleecan Machine 저장 완료: {output_path}")


def cmd_info(args) -> int:
    """info 명령어 핸들러 — 빠른 기본 정보 출력."""
    dxf_path = args.dxf_file

    if not os.path.isfile(dxf_path):
        print(f"[오류] 파일을 찾을 수 없습니다: {dxf_path}", file=sys.stderr)
        return 1

    origin = (args.origin[0], args.origin[1]) if args.origin else (0.0, 0.0)

    from pipeline import analyze_dxf_v2

    result = analyze_dxf_v2(
        dxf_path,
        origin=origin,
        n_poles=args.poles,
        n_slots=args.slots,
        enable_radius_fallback=args.enable_radius_fallback,
        fallback_r_shaft_mm=args.fallback_shaft,
        fallback_r_stator_outer_mm=args.fallback_stator_outer,
        verbose=False,
    )
    dims = result.get('dims', {})

    print(f"파일       : {os.path.basename(dxf_path)}")
    print(f"극수/슬롯수: {dims.get('n_poles')}P / {dims.get('n_slots')}S")
    print(f"토폴로지   : {dims.get('topology', 'UNKNOWN')}")
    print(f"에어갭     : {dims.get('airgap_mm', 0):.3f} mm")
    print(f"로터 외경  : {dims.get('r_rotor_outer_mm', 0):.3f} mm")
    print(f"스테이터 외경: {dims.get('r_stator_outer_mm', 0):.3f} mm")
    print(f"자석 그룹  : {dims.get('n_magnet_groups', 0)}  배리어: {dims.get('n_barriers', 0)}")
    return 0


def cmd_version(_args) -> int:
    """version 명령어 핸들러."""
    from . import __version__
    print(f"pyMotorGeo {__version__}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='pymotorgeo',
        description='pyMotorGeo — 모터 DXF 기하구조 자동 분석',
    )
    sub = parser.add_subparsers(dest='command', metavar='<command>')
    sub.required = True

    # ── analyze ──
    p_analyze = sub.add_parser('analyze', help='DXF 파일 전체 분석')
    p_analyze.add_argument('dxf_file', metavar='DXF',
                           help='분석할 DXF 파일 경로')
    p_analyze.add_argument('--poles',  type=int, default=None, metavar='N',
                           help='극수 강제 지정 (미지정 시 자동 추정)')
    p_analyze.add_argument('--slots',  type=int, default=None, metavar='N',
                           help='슬롯수 강제 지정 (미지정 시 자동 추정)')
    p_analyze.add_argument('--origin', type=float, nargs=2, metavar=('X', 'Y'),
                           default=None, help='회전 원점 좌표 (기본: 0 0)')
    p_analyze.add_argument('--export', choices=['json', 'pyleecan'], default=None,
                           help='결과 내보내기 형식')
    p_analyze.add_argument('--output', default=None, metavar='PATH',
                           help='내보내기 파일 경로 (미지정 시 자동 생성)')
    p_analyze.add_argument('--quiet', '-q', action='store_true',
                           help='진행 메시지 숨김')
    p_analyze.add_argument('--enable-radius-fallback', action='store_true',
                           help='반경 추정 실패 시 fallback으로 close 단계를 계속 진행')
    p_analyze.add_argument('--fallback-shaft', type=float, default=None, metavar='MM',
                           help='샤프트 반경 fallback (mm)')
    p_analyze.add_argument('--fallback-stator-outer', type=float, default=None, metavar='MM',
                           help='스테이터 외경 fallback (mm)')
    p_analyze.set_defaults(func=cmd_analyze)

    # ── info ──
    p_info = sub.add_parser('info', help='기본 정보만 빠르게 출력')
    p_info.add_argument('dxf_file', metavar='DXF',
                        help='분석할 DXF 파일 경로')
    p_info.add_argument('--poles',  type=int, default=None, metavar='N')
    p_info.add_argument('--slots',  type=int, default=None, metavar='N')
    p_info.add_argument('--origin', type=float, nargs=2, metavar=('X', 'Y'),
                        default=None)
    p_info.add_argument('--enable-radius-fallback', action='store_true')
    p_info.add_argument('--fallback-shaft', type=float, default=None, metavar='MM')
    p_info.add_argument('--fallback-stator-outer', type=float, default=None, metavar='MM')
    p_info.set_defaults(func=cmd_info)

    # ── version ──
    p_ver = sub.add_parser('version', help='버전 출력')
    p_ver.set_defaults(func=cmd_version)

    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == '__main__':
    main()
