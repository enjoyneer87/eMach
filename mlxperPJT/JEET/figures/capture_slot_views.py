"""
Motor-CAD API를 이용한 슬롯 단면 + 권선 뷰 캡처
JEETResult_MCAD.m 참조: mcad.SaveScreenToFile("StatorWinding", path)
Python API: mcad.save_screen_to_file("StatorWinding", path)
"""
import sys
import os
import io

# UTF-8 인코딩 강제 (Korean Windows cp949 환경 대비)
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from ansys.motorcad.core import MotorCAD

MOT_FILES = {
    "4turn": r"D:\KangDH\Thesis\e10\refModel\e10Turn4V261.mot",
    "6turn": r"D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot",
    "8turn": r"D:\KangDH\Thesis\e10\refModel\e10Turn8V261.mot",
}
OUT_DIR = r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\figures"

# 저장할 캡처 컨텍스트 목록
# SaveScreenToFile(context, path) — context 문자열:
#   "Radial"        : Geometry 탭 Radial 단면
#   "StatorWinding" : Winding 탭 권선 단면 (원하는 뷰)
CAPTURE_CONTEXTS = [
    ("StatorWinding", "winding"),   # 권선 단면 — 도체 배치 확인
    ("Radial",        "radial"),    # 형상 단면 — 기존 뷰
]

os.makedirs(OUT_DIR, exist_ok=True)


def save_screen(mcad, context, out_path):
    """SaveScreenToFile(context, path) — MATLAB/Python 공통 API"""
    try:
        # Python ansys.motorcad.core API (snake_case)
        mcad.save_screen_to_file(context, out_path)
        print(f"  [OK] save_screen_to_file('{context}') -> {out_path}")
        return True
    except Exception as e1:
        print(f"  [WARN] save_screen_to_file 실패: {e1}")
    try:
        # MATLAB COM API 직접 호출 (camelCase fallback)
        mcad.SaveScreenToFile(context, out_path)
        print(f"  [OK] SaveScreenToFile('{context}') -> {out_path}")
        return True
    except Exception as e2:
        print(f"  [ERROR] SaveScreenToFile 실패: {e2}")
    return False


for label, mot_path in MOT_FILES.items():
    print(f"\n=== {label}: {mot_path} ===")

    if not os.path.exists(mot_path):
        print(f"  [SKIP] 파일 없음: {mot_path}")
        continue

    try:
        mcad = MotorCAD(open_new_instance=True, enable_exceptions=True)
        mcad.load_from_file(mot_path)
        print(f"  [OK] Loaded")

        try:
            mcad.set_variable("MessageDisplayState", 0)
        except Exception:
            pass

        # 각 컨텍스트 캡처
        for ctx, suffix in CAPTURE_CONTEXTS:
            out_path = os.path.join(OUT_DIR, f"slot_{suffix}_{label}.png")
            save_screen(mcad, ctx, out_path)

        # 도체 치수 출력 (8턴 클램핑 확인)
        try:
            w = mcad.get_variable("ConductorWidth")
            h = mcad.get_variable("ConductorHeight")
            print(f"  [INFO] Conductor: W={w:.4f} mm  H={h:.4f} mm")
        except Exception as e:
            print(f"  [WARN] 도체 치수 읽기 실패: {e}")

        mcad.quit()

    except Exception as e:
        print(f"  [ERROR] {label}: {e}")
        import traceback
        traceback.print_exc()

print("\n=== Done! ===")
print(f"저장 위치: {OUT_DIR}")
