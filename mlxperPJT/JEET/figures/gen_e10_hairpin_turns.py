"""
gen_e10_hairpin_turns.py
========================
Ref(6턴, e10Turn6V261.mot) 기반으로 4턴/8턴 헤어핀 .mot 파일 생성

※ 헤어핀 권선에서 '턴수 = 슬롯당 도체(바) 수 = WindingLayers' 로 정의된다.
  (각 바 = 1턴 → MagTurnsConductor 는 1로 고정, 변경 대상 아님)
  도체 geometry는 wire-size 모드(Armature_Winding_Definition_Hairpin=0)로
  Copper_Width / Copper_Height 로 정의된다 (ratio_array 아님).

도체 사이징 로직 (점적율 보존):
  ※ 기존 검증 코드 SkkuEMLabProject\\calcConductorSize.m 의 알고리즘을 그대로 이식.
  ※ Motor-CAD 가 계산한 실제 슬롯 면적을 GetVariable 로 읽어 사이징 (MCAD-native).

    effective_FF  = Area_Slot * FF_copper(%) / Area_Winding_With_Liner
    eff_slot_area = Area_Winding_With_Liner * effective_FF/100
    turn_area     = eff_slot_area / WindingLayers          # 도체 1개당 copper 면적
    Copper_Width  = Slot_Width - 2*Liner - 2*Insul - 2*Sep # 슬롯폭에 맞춤(고정)
    Copper_Height = turn_area / Copper_Width               # 면적/너비
    # Winding_Depth 기반 높이 상한 클램프 (도체수 N 으로 일반화)
    max_H = (Winding_Depth - Liner - 2*N*Insul - (N+1)*Sep) / N

  목표 점적율(FF_copper)은 기준(6턴) 모델의 GrossSlotFillFactor 를 그대로 사용
  → 턴수만 바꾸고 copper 점적율은 동일하게 유지.

  변수명은 Motor-CAD ActiveXParameters v261
  (eMach\\ActiveXParametersMotorCADv261.txt) 기준.

사용법:
  python gen_e10_hairpin_turns.py
  ※ Motor-CAD가 설치되어 있어야 함 (COM 인터페이스 사용)
  ※ win32com(pywin32)이 있는 인터프리터 필요 (pyMotorEnv_310 venv)

출력:
  D:\\KangDH\\Thesis\\e10\\refModel\\e10Turn4V261.mot
  D:\\KangDH\\Thesis\\e10\\refModel\\e10Turn8V261.mot
"""

from ansys.motorcad.core import MotorCAD
import os
import sys

# Windows 콘솔(cp949)에서 ✓/─ 등 유니코드 출력 시 UnicodeEncodeError 방지
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# ============================================================
# 설정
# ============================================================
MOT_BASE = r'D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot'
OUT_DIR  = r'D:\KangDH\Thesis\e10\refModel'
BASE_TURNS   = 6
TARGET_TURNS = [4, 8]   # 새 WindingLayers (슬롯당 도체수) 목록


# ============================================================
# COM 유틸리티
# ============================================================

def get_var(mcad, name, default=None):
    """변수 읽기 (없으면 default 반환). ansys.motorcad.core 는 값을 직접 반환."""
    try:
        val = mcad.get_variable(name)
        if isinstance(val, (list, tuple)):
            val = val[-1]
        return val
    except Exception:
        return default


def get_num(mcad, name, default=None):
    """숫자 변수 읽기 (float)."""
    v = get_var(mcad, name, None)
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def set_var(mcad, name, value):
    """변수 쓰기 (ansys.motorcad.core: 예외만 처리)."""
    try:
        mcad.set_variable(name, value)
    except Exception as e:
        print(f"  [오류] set_variable({name}={value}): {e}")


def recompute_geometry(mcad):
    """형상 재계산/검증 (슬롯 면적 등 o/p 갱신). edit_geometry=1: 유효화 시도."""
    try:
        return mcad.check_if_geometry_is_valid(1)
    except Exception as e:
        print(f"  [경고] check_if_geometry_is_valid 실패: {e}")
        return None


# ============================================================
# 파라미터 읽기
# ============================================================

def read_params(mcad):
    """헤어핀 권선 및 슬롯 관련 파라미터 읽기 (v261 변수명)."""
    p = {}

    # 권선 정의 (헤어핀: 턴수 = WindingLayers)
    p['Ncond']        = int(get_num(mcad, 'WindingLayers', 0))      # 슬롯당 도체수=턴수 (변경 대상)
    p['TurnsPerCoil'] = int(get_num(mcad, 'MagTurnsConductor', 1))  # 코일당 턴수 (헤어핀=1, 참고)
    p['Parallel']     = int(get_num(mcad, 'ParallelPaths_Hairpin', 1))
    p['Slots']        = int(get_num(mcad, 'Slot_Number', 0))
    p['Poles']        = int(get_num(mcad, 'Pole_Number', 0))

    # 도체(구리 바) 치수 — wire-size 모드
    p['Copper_W'] = get_num(mcad, 'Copper_Width', None)
    p['Copper_H'] = get_num(mcad, 'Copper_Height', None)

    # 슬롯/절연 치수 (사이징 입력)
    p['Slot_Width']   = get_num(mcad, 'Slot_Width', None)
    p['Liner']        = get_num(mcad, 'Liner_Thickness', 0.0) or 0.0
    p['Insul']        = get_num(mcad, 'Insulation_Thickness', 0.0) or 0.0
    p['Separation']   = get_num(mcad, 'ConductorSeparation', 0.0) or 0.0

    # 슬롯 면적/깊이 (o/p — 형상 재계산 후 유효)
    p['Area_Slot']      = get_num(mcad, 'Area_Slot', None)
    p['Area_Wdg_Liner'] = get_num(mcad, 'Area_Winding_With_Liner', None)
    p['Winding_Depth']  = get_num(mcad, 'Winding_Depth', None)

    # 점적율 (copper/slot, o/p) — 목표 점적율의 기준
    p['GrossFill'] = get_num(mcad, 'GrossSlotFillFactor', None)

    return p


def print_params(p):
    """기준 모델 파라미터 출력."""
    print("\n  [현재 기준 모델 파라미터]")
    print(f"    WindingLayers(도체수/턴수): {p['Ncond']}   [변경 대상]")
    print(f"    MagTurnsConductor         : {p['TurnsPerCoil']}   (코일당 턴수, 헤어핀=1, 고정)")
    print(f"    ParallelPaths_Hairpin     : {p['Parallel']}")
    print(f"    Slots / Poles             : {p['Slots']} / {p['Poles']}")
    print(f"    Copper_Width  / Height    : {p['Copper_W']:.4f} / {p['Copper_H']:.4f} mm")
    print(f"    도체 단면적(W×H)          : {p['Copper_W'] * p['Copper_H']:.4f} mm²")
    print(f"    슬롯당 총 copper 면적     : {p['Copper_W'] * p['Copper_H'] * p['Ncond']:.4f} mm²")
    print(f"    Slot_Width                : {p['Slot_Width']:.4f} mm")
    print(f"    Liner / Insul / Separation: {p['Liner']:.3f} / {p['Insul']:.3f} / {p['Separation']:.3f} mm")
    print(f"    Area_Slot                 : {p['Area_Slot']}")
    print(f"    Area_Winding_With_Liner   : {p['Area_Wdg_Liner']}")
    print(f"    Winding_Depth             : {p['Winding_Depth']}")
    print(f"    GrossSlotFillFactor (목표): {p['GrossFill']}")


# ============================================================
# 도체 사이징 (calcConductorSize.m 이식)
# ============================================================

def calc_conductor_size(geom, new_N, target_ff_pct):
    """
    점적율 보존 copper 치수 계산 (SkkuEMLabProject\\calcConductorSize.m 이식).

    geom         : 형상 재계산 후 읽은 슬롯/절연 파라미터 dict
                   (Area_Slot, Area_Wdg_Liner, Slot_Width, Winding_Depth,
                    Liner, Insul, Separation, Copper_W)
    new_N        : 새 도체수 (WindingLayers)
    target_ff_pct: 목표 copper 점적율 [%]  (기준 모델 GrossSlotFillFactor×100)
    """
    Area_Slot  = geom['Area_Slot']
    Area_WdgL  = geom['Area_Wdg_Liner']
    Slot_Width = geom['Slot_Width']
    Wdg_Depth  = geom['Winding_Depth']
    Liner      = geom['Liner']
    Insul      = geom['Insul']
    Sep        = geom['Separation']

    # 점적율 환산 (slot-area 기준 → winding-area 기준)
    effective_ff = Area_Slot * target_ff_pct / Area_WdgL        # [%]
    eff_slot_area = Area_WdgL * (effective_ff / 100.0)
    turn_area     = eff_slot_area / new_N                       # 도체 1개당 copper 면적

    # 너비: 슬롯폭 - 양측 라이너/절연/도체간격
    Copper_W = Slot_Width - 2 * Liner - 2 * Insul - 2 * Sep
    # 높이: 면적 / 너비
    Copper_H = turn_area / Copper_W

    # 높이 상한 (Winding_Depth 안에 N개 적층 가능한 최대 copper 높이)
    # 공식 Ansys 문서(Logic of Coil Sizing... p11) 기준:
    #   가용 copper 적층 공간 = Dw - 2·I·N - S(N+1)
    #   ※ Dw(Winding_Depth)는 이미 라이너 제외값(Dw = Ds - L)이므로 Liner를 또 빼지 않는다.
    #     (calcConductorSize.m 원본은 Liner를 이중 차감 + 도체수 10 하드코딩 → 여기서 교정)
    max_H = (Wdg_Depth - 2 * new_N * Insul - (new_N + 1) * Sep) / new_N
    clamped = False
    if Copper_H > max_H:
        Copper_H = max_H
        clamped = True

    return {
        'Copper_W': Copper_W,
        'Copper_H': Copper_H,
        'turn_area': turn_area,
        'effective_ff': effective_ff,
        'max_H': max_H,
        'clamped': clamped,
    }


# ============================================================
# 메인
# ============================================================

def main():
    print("=" * 65)
    print("  헤어핀 턴수(WindingLayers) 변환 Motor-CAD .mot 생성기")
    print(f"  기준: {MOT_BASE}")
    print(f"  대상 도체수: {TARGET_TURNS} (기준 {BASE_TURNS})")
    print("  사이징: 점적율 보존 (calcConductorSize.m 로직)")
    print("=" * 65)

    # Motor-CAD 연결
    print("\nMotor-CAD COM 인터페이스 연결 중...")
    try:
        mcad = MotorCAD()
    except Exception as e:
        print(f"[오류] Motor-CAD 연결 실패: {e}")
        print("  → Motor-CAD가 설치되어 있는지 확인하세요.")
        sys.exit(1)

    # GUI 표시 (실패해도 무시)
    try:
        mcad.set_visible(True)
    except Exception:
        pass

    # 기준 파일 열기 + 형상 재계산
    print(f"기준 파일 열기: {MOT_BASE}")
    mcad.load_from_file(MOT_BASE)
    recompute_geometry(mcad)

    # 현재(기준) 파라미터 읽기
    p = read_params(mcad)
    print_params(p)

    # 필수값 확인
    required = ['Copper_W', 'Copper_H', 'Slot_Width', 'Area_Slot',
                'Area_Wdg_Liner', 'Winding_Depth', 'GrossFill', 'Ncond']
    missing = [k for k in required if p.get(k) in (None, 0)]
    if missing:
        print(f"\n[오류] 기준 모델에서 필수 변수를 읽지 못했습니다: {missing}")
        print("  → 변수명/형상 유효성(CheckIfGeometryIsValid)을 확인하세요.")
        mcad.quit()
        sys.exit(1)

    # 목표 점적율 = 기준 모델 GrossSlotFillFactor (copper/slot)
    target_ff_pct = p['GrossFill'] * 100.0 if p['GrossFill'] <= 1.0 else p['GrossFill']
    print(f"\n  ▶ 목표 copper 점적율(고정): {target_ff_pct:.3f} %  (기준 모델값)")

    # 각 도체수에 대해 .mot 생성
    generated = []
    for new_N in TARGET_TURNS:
        print(f"\n{'─'*55}")
        print(f"  ▶  도체수(WindingLayers) {new_N} 변환 (기준 {BASE_TURNS})")

        # 기준 파일 재로드 (이전 변경 초기화)
        mcad.load_from_file(MOT_BASE)

        # 1) 턴수(도체수) 적용 후 형상 재계산
        set_var(mcad, 'WindingLayers', new_N)
        recompute_geometry(mcad)

        applied = get_num(mcad, 'WindingLayers')
        if applied is None or int(applied) != new_N:
            print(f"    [오류] 도체수 적용 실패: WindingLayers={applied} (기대 {new_N}) — 건너뜀")
            continue

        # 2) 현재 슬롯 형상 재독 (도체수 변경 반영된 Area/Depth)
        g = read_params(mcad)

        # 3) 점적율 보존 copper 사이징
        r = calc_conductor_size(g, new_N, target_ff_pct)

        print(f"    Copper_Width  : {g['Copper_W']:.4f} → {r['Copper_W']:.4f} mm")
        print(f"    Copper_Height : {g['Copper_H']:.4f} → {r['Copper_H']:.4f} mm")
        print(f"    도체 1개 면적 : {r['turn_area']:.4f} mm²  (목표)")
        print(f"    effective_FF  : {r['effective_ff']:.3f} %")
        if r['clamped']:
            print(f"    [주의] 높이가 Winding_Depth 상한({r['max_H']:.4f} mm)으로 클램프됨 "
                  f"→ 목표 점적율 미달 가능")

        # 4) copper 치수 적용 후 형상 재계산
        set_var(mcad, 'Copper_Width',  r['Copper_W'])
        set_var(mcad, 'Copper_Height', r['Copper_H'])
        recompute_geometry(mcad)

        # 5) 형상 유효성 + 실제 점적율 확인
        valid = recompute_geometry(mcad)
        new_fill = get_num(mcad, 'GrossSlotFillFactor')
        print(f"    형상 유효성   : {valid}")
        print(f"    실제 점적율   : {new_fill}  (목표 {target_ff_pct/100:.4f})")

        # 6) 저장
        out_name = f'e10Turn{new_N}V261.mot'
        out_path = os.path.join(OUT_DIR, out_name)
        mcad.save_to_file(out_path)

        if os.path.exists(out_path):
            size_kb = os.path.getsize(out_path) / 1024
            print(f"    ✓ 저장: {out_path}  ({size_kb:.1f} KB)")
            generated.append(out_path)
        else:
            print(f"    [오류] 저장 실패: {out_path}")

    # 결과 요약
    print(f"\n{'='*65}")
    print("  완료! 생성된 파일:")
    for path in generated:
        print(f"    {path}")

    print("""
  다음 단계:
    1. Motor-CAD에서 각 .mot 파일 열어 슬롯 geometry 육안 확인
       (Copper_Width/Height, 점적율이 의도대로인지)
    2. gen_e10_satumap_from_mot.m 을 각 파일에 적용하여 SatuMap 생성
       예: motPath = 'D:\\KangDH\\Thesis\\e10\\refModel\\e10Turn4V261.mot';
    3. AC 손실 LAB 시뮬레이션 실행 → RBF 학습용 Kturn 데이터 확보
    """)

    print("Motor-CAD를 종료하지 않음 (자동 실행 모드: 직접 종료하세요)")


if __name__ == '__main__':
    main()
