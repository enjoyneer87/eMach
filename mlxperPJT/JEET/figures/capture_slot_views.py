"""
Motor-CAD API를 이용한 슬롯 단면 + 권선 뷰 캡처

API: initialise_tab_names() → save_motorcad_screen_to_file("Geometry;Winding", path)
도큐: https://motorcad.docs.pyansys.com/version/stable/methods/_autosummary_UI/
      ansys.motorcad.core.motorcad_methods.MotorCAD.save_motorcad_screen_to_file.html

save_motorcad_screen_to_file(screen_name, file_name):
  - screen_name 형식: "tabName;SubTab" (예: "Geometry;Axial", "Geometry;Winding")
  - 호출 전 initialise_tab_names() 필수
  - Motor-CAD UI visible 상태 필요 (set_visible(True))
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

# 저장할 탭 캡처 목록
# save_motorcad_screen_to_file(screen_name, file) — screen_name = "Tab;SubTab"
#   "Geometry;Winding" : 권선 배치 탭 (턴수·도체 배치 확인) ← 핵심
#   "Geometry;Axial"   : 축방향 단면 뷰
#   ⚠️ "Geometry;Winding" 은 존재하지 않는 조합 → 항상 실패했음.
#      Motor-CAD v2026.1.1 기준 Winding 은 Geometry 의 하위탭이 아니라 최상위 탭이고,
#      Geometry 의 하위탭은 Radial / Axial / Editor / 3D 이다.
#      2026-07-20 실측으로 유효 확인: Winding;Definition, Winding;Pattern, Geometry;Radial
CAPTURE_TABS = [
    ("Winding;Definition", "winding"),  # ← 핵심: 슬롯 단면 + 도체 치수/점적율 표
    ("Winding;Pattern",    "pattern"),  # 권선 패턴
    ("Geometry;Radial",    "radial"),   # 반경방향 슬롯 단면
]

os.makedirs(OUT_DIR, exist_ok=True)


def save_screen_tab(mcad, tab_name, out_path):
    """save_motorcad_screen_to_file API. initialise_tab_names() 선행 필수."""
    try:
        mcad.initialise_tab_names()
        mcad.save_motorcad_screen_to_file(tab_name, out_path)
        print(f"  [OK] save_motorcad_screen_to_file('{tab_name}') -> {out_path}")
        return True
    except Exception as e:
        print(f"  [ERROR] save_motorcad_screen_to_file('{tab_name}'): {e}")
        return False


for label, mot_path in MOT_FILES.items():
    print(f"\n=== {label}: {mot_path} ===")

    if not os.path.exists(mot_path):
        print(f"  [SKIP] 파일 없음: {mot_path}")
        continue

    try:
        # 기존 COM 인스턴스 충돌 방지: open_new_instance=True
        mcad = MotorCAD(open_new_instance=True, enable_exceptions=True)
        mcad.set_visible(True)   # UI 표시 필수 (save_motorcad_screen_to_file 요구)
        mcad.load_from_file(mot_path)
        print(f"  [OK] Loaded")

        try:
            mcad.set_variable("MessageDisplayState", 0)
        except Exception:
            pass

        # 각 탭 캡처
        for tab_name, suffix in CAPTURE_TABS:
            out_path = os.path.join(OUT_DIR, f"slot_{suffix}_{label}.png")
            save_screen_tab(mcad, tab_name, out_path)

        # 도체 치수 + 턴수 확인 (8턴 클램핑 체크)
        try:
            w = mcad.get_variable("Copper_Width")
            h = mcad.get_variable("Copper_Height")
            n = int(mcad.get_variable("WindingLayers"))
            fill = mcad.get_variable("GrossSlotFillFactor")
            print(f"  [INFO] WindingLayers={n}  Copper W={w:.4f} mm  H={h:.4f} mm  Fill={fill:.4f}")
        except Exception as e:
            print(f"  [WARN] 치수 읽기 실패: {e}")

        mcad.quit()

    except Exception as e:
        print(f"  [ERROR] {label}: {e}")
        import traceback
        traceback.print_exc()

print("\n=== Done! ===")
print(f"저장 위치: {OUT_DIR}")
