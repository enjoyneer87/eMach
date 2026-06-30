"""
gen_e10_hairpin_turns.py
========================
Ref(6턴, e10Turn6V261.mot) 기반으로 4턴/8턴 헤어핀 .mot 파일 생성

설계 조건:
  1. 점적율 유지: 도체 단면적 × 슬롯당 도체수 = const
     → 도체 높이(H)를 턴수에 반비례하게 스케일링 (너비는 슬롯폭 제약으로 고정)
     → H_new = H_old × (N_old / N_new)

  2. 슬롯 내 코일 시작점 위치 유지:
     슬롯 내 도체 배열 구조 (슬롯오프닝 → 슬롯바닥):
       [슬롯오프닝] ─ [웨지/라이너] ─ [슬롯절연] ─ [도체1, 도체2, ...] ─ [하부절연] ─ [슬롯바닥]

     첫 도체 시작점 = SlotOpening + WedgeThickness + SlotLinerThickness + SlotInsulation
     → 이 값은 라이너/절연물을 그대로 두면 턴수와 무관하게 고정됨 ✓
     → 슬롯오프닝 가까운 도체가 회전자 자속의 영향을 동일하게 받음

  3. 도체 너비는 슬롯 폭 방향 제약으로 변경 안 함
     (슬롯 양쪽 절연물 사이 공간에 꼭 맞게 이미 설계됨)

사용법:
  python gen_e10_hairpin_turns.py
  ※ Motor-CAD가 설치되어 있어야 함 (COM 인터페이스 사용)

출력:
  D:\\KangDH\\Thesis\\e10\\refModel\\e10Turn4V261.mot
  D:\\KangDH\\Thesis\\e10\\refModel\\e10Turn8V261.mot
"""

import win32com.client
import os
import sys
from pathlib import Path

# ============================================================
# 설정
# ============================================================
MOT_BASE = r'D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot'
OUT_DIR  = r'D:\KangDH\Thesis\e10\refModel'
BASE_TURNS   = 6
TARGET_TURNS = [4, 8]

# Motor-CAD 버전에 따른 도체 치수 변수명 후보 (우선순위 순)
COND_H_CANDIDATES = [
    'ConductorHeight',       # v14+
    'HalfPinHeight',         # 일부 버전
    'WireHeight',
    'BarHeight',
    'Hairpin_Cond_Height',
]
COND_W_CANDIDATES = [
    'ConductorWidth',
    'HalfPinWidth',
    'WireWidth',
    'BarWidth',
    'Hairpin_Cond_Width',
]


# ============================================================
# 유틸리티
# ============================================================

def get_var(mcad, name, default=None):
    """변수 읽기 (없으면 default 반환)"""
    try:
        val = mcad.GetVariable(name)
        return val
    except Exception:
        return default


def set_var(mcad, name, value):
    """변수 쓰기 (반환값 확인)"""
    try:
        ret = mcad.SetVariable(name, value)
        if ret != 0:
            print(f"  [경고] SetVariable({name}={value}) → ret={ret}")
    except Exception as e:
        print(f"  [오류] SetVariable({name}={value}): {e}")


def find_var(mcad, candidates):
    """후보 변수명 목록 중 실제 존재하는 첫 번째 변수 반환"""
    for name in candidates:
        val = get_var(mcad, name)
        if val is not None:
            return name, float(val)
    return None, None


# ============================================================
# 파라미터 읽기
# ============================================================

def read_params(mcad):
    """헤어핀 권선 및 슬롯 관련 파라미터 읽기"""
    p = {}

    # 기본 권선
    p['Turns']  = int(get_var(mcad, 'Winding_Turns', 0))
    p['Layers'] = int(get_var(mcad, 'Winding_Layers', 2))
    p['Phases'] = int(get_var(mcad, 'Winding_Phases', 3))
    p['Slots']  = int(get_var(mcad, 'Stator_Slots', 0))
    p['Poles']  = int(get_var(mcad, 'Pole_Number', 0))

    # 도체 치수
    p['H_var'], p['H'] = find_var(mcad, COND_H_CANDIDATES)
    p['W_var'], p['W'] = find_var(mcad, COND_W_CANDIDATES)

    # 도체 간 절연 (각 도체 주변 에나멜 등)
    p['CondInsul'] = get_var(mcad, 'ConductorInsulationThickness', 0.0) or 0.0

    # 슬롯 내 절연/라이너 (슬롯벽 ~ 도체 사이)
    # ※ 이 값들이 코일 시작점을 결정 → 변경하지 않음
    p['SlotInsul']  = get_var(mcad, 'Slot_Insulation_Thickness', 0.0) or 0.0
    p['WedgeThick'] = get_var(mcad, 'WedgeThickness', 0.0) or 0.0
    p['SlotLiner']  = get_var(mcad, 'SlotLinerThickness', 0.0) or 0.0

    # 슬롯 오프닝
    p['SlotOpening'] = get_var(mcad, 'Stator_Slot_Opening', None)

    # 점적율 (참고)
    p['FillFactor'] = get_var(mcad, 'Slot_Fill_Factor', None)

    return p


def print_params(p):
    """파라미터 출력"""
    print("\n  [현재 기준 모델 파라미터]")
    print(f"    Turns / Layers     : {p['Turns']} / {p['Layers']}")
    print(f"    Slots / Poles      : {p['Slots']} / {p['Poles']}")
    print(f"    Slots/pole/phase   : {p['Slots'] / p['Poles'] / p['Phases']:.1f}")
    print(f"    ConductorHeight    : {p['H']:.4f} mm  [변수: {p['H_var']}]")
    print(f"    ConductorWidth     : {p['W']:.4f} mm  [변수: {p['W_var']}]")
    print(f"    도체 단면적        : {p['H'] * p['W']:.4f} mm²")
    print(f"    슬롯당 총 도체수   : {p['Turns'] * p['Layers']}")
    print(f"    CondInsulation     : {p['CondInsul']:.4f} mm (도체 에나멜)")
    print(f"    SlotInsulation     : {p['SlotInsul']:.4f} mm")
    print(f"    WedgeThickness     : {p['WedgeThick']:.4f} mm")
    print(f"    SlotLiner          : {p['SlotLiner']:.4f} mm")
    if p['SlotOpening'] is not None:
        print(f"    Slot Opening       : {p['SlotOpening']:.4f} mm")
    print(f"    FillFactor (현재)  : {p['FillFactor']}")

    # 코일 시작점 추정 (슬롯오프닝 기준)
    coil_start = (p['WedgeThick'] + p['SlotLiner'] + p['SlotInsul'])
    print(f"\n  [코일 시작점] 슬롯오프닝 끝에서 {coil_start:.3f} mm 이후 첫 도체 시작")
    print(f"    (웨지={p['WedgeThick']}mm + 라이너={p['SlotLiner']}mm + 슬롯절연={p['SlotInsul']}mm)")
    print(f"    ※ 이 값은 턴수 변경과 무관하게 동일 유지됨")


# ============================================================
# 치수 계산
# ============================================================

def calc_new_conductor(p, new_turns):
    """
    새 턴수에 맞는 도체 높이 계산

    조건: 슬롯 내 총 도체 단면적 = const
    → H_new × N_cond_new = H_old × N_cond_old
    → H_new = H_old × (N_cond_old / N_cond_new)
       (N_cond = Turns × Layers, W_cond 고정 가정)
    """
    n_old = p['Turns']  * p['Layers']
    n_new = new_turns   * p['Layers']
    ratio = n_old / n_new

    H_new = p['H'] * ratio
    W_new = p['W']   # 너비 고정

    # 순수 도체 면적 합 (CondInsul 제외)
    area_old = p['W'] * p['H']   * n_old
    area_new = W_new  * H_new    * n_new
    fill_ratio = area_new / area_old

    # 도체 + 절연 포함 스택 높이
    stack_old = (p['H'] + 2*p['CondInsul']) * p['Turns']   # 한 레이어 기준
    stack_new = (H_new  + 2*p['CondInsul']) * new_turns

    return {
        'H': H_new,
        'W': W_new,
        'H_ratio': ratio,
        'fill_ratio': fill_ratio,
        'stack_old_mm': stack_old,
        'stack_new_mm': stack_new,
    }


def check_feasibility(p, new_turns, result):
    """물리적 실현 가능성 체크"""
    issues = []

    # 도체 너비 최소 체크 (보통 0.5mm 미만은 헤어핀 불가)
    if result['H'] < 0.5:
        issues.append(f"도체 높이 {result['H']:.3f} mm < 0.5 mm (헤어핀 제작 한계)")

    # 너비 > 높이 비율 체크 (헤어핀 최적 비율)
    aspect = result['W'] / result['H']
    if aspect > 5:
        issues.append(f"도체 종횡비 W/H={aspect:.2f} > 5 (헤어핀 구조적 취약)")

    # 스택 높이 증가 경고 (4턴 → 더 큰 도체)
    if result['stack_new_mm'] > result['stack_old_mm'] * 1.1:
        issues.append(
            f"슬롯 내 도체 스택 높이 {result['stack_new_mm']:.3f} mm "
            f"(기준 {result['stack_old_mm']:.3f} mm +{result['stack_new_mm']/result['stack_old_mm']-1:.1%})"
        )

    return issues


# ============================================================
# 메인
# ============================================================

def main():
    print("=" * 65)
    print("  헤어핀 턴수 변환 Motor-CAD .mot 생성기")
    print(f"  기준: {MOT_BASE}")
    print(f"  대상 턴수: {TARGET_TURNS}")
    print("=" * 65)

    # Motor-CAD 연결
    print("\nMotor-CAD COM 인터페이스 연결 중...")
    try:
        mcad = win32com.client.Dispatch('MotorCAD.AppAutomation')
    except Exception as e:
        print(f"[오류] Motor-CAD COM 연결 실패: {e}")
        print("  → Motor-CAD가 설치되어 있는지 확인하세요.")
        sys.exit(1)

    mcad.Visible = True

    # 기준 파일 열기
    print(f"기준 파일 열기: {MOT_BASE}")
    mcad.OpenFile(MOT_BASE)

    # 현재 파라미터 읽기
    p = read_params(mcad)
    print_params(p)

    if p['H_var'] is None or p['W_var'] is None:
        print("\n[오류] 도체 치수 변수를 찾지 못했습니다.")
        print("  → Motor-CAD 버전에 맞는 변수명을 COND_H_CANDIDATES에 추가하세요.")
        print("  → Motor-CAD GUI에서 Winding > Conductor Dimensions 탭의 변수명을 확인하세요.")
        mcad.Quit()
        sys.exit(1)

    # 각 턴수에 대해 .mot 생성
    generated = []
    for new_turns in TARGET_TURNS:
        print(f"\n{'─'*55}")
        print(f"  ▶  {new_turns}턴 변환 (기준 {BASE_TURNS}턴)")

        result = calc_new_conductor(p, new_turns)

        print(f"    도체 높이  : {p['H']:.4f} → {result['H']:.4f} mm  (×{result['H_ratio']:.4f})")
        print(f"    도체 너비  : {result['W']:.4f} mm  (고정)")
        print(f"    이론 점적율: {result['fill_ratio']:.4f}  (1.0 = 완전 유지)")
        print(f"    도체 스택  : {result['stack_old_mm']:.3f} mm → {result['stack_new_mm']:.3f} mm (1레이어)")

        # 실현 가능성 체크
        issues = check_feasibility(p, new_turns, result)
        if issues:
            print("    [주의]")
            for iss in issues:
                print(f"      ⚠  {iss}")
        else:
            print("    ✓ 치수 적합")

        # 기준 파일 재로드 (이전 변경 초기화)
        mcad.OpenFile(MOT_BASE)

        # 파라미터 적용
        set_var(mcad, 'Winding_Turns', new_turns)
        set_var(mcad, p['H_var'], result['H'])
        # 너비는 변경 없음 (이미 기준값 그대로)

        # Motor-CAD 내부 재계산 대기
        # (필요 시 mcad.DoWeightCalculation() 등 추가)

        # 적용 후 점적율 확인
        new_fill = get_var(mcad, 'Slot_Fill_Factor')
        print(f"    실제 점적율: {new_fill}  (Motor-CAD 계산값)")

        # 저장
        out_name = f'e10Turn{new_turns}V261.mot'
        out_path = os.path.join(OUT_DIR, out_name)
        mcad.SaveToFile(out_path)

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
    2. gen_e10_satumap_from_mot.m 을 4/8턴 파일에 적용하여 SatuMap 생성
       예: motPath = 'D:\\KangDH\\Thesis\\e10\\refModel\\e10Turn4V261.mot';
    3. AC 손실 LAB 시뮬레이션 실행 → RBF 학습용 데이터 확보
    """)

    print("Motor-CAD를 종료하지 않음 (자동 실행 모드: 직접 종료하세요)")


if __name__ == '__main__':
    main()
