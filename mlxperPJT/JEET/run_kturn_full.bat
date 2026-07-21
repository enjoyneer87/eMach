@echo off
chcp 65001 >nul
set PYTHON=C:\Users\user\.ansys_python_venvs\pyMotorEnv_310\Scripts\python.exe
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo ============================================================
echo  JEET Kturn 전체 파이프라인 (캡처 → 4턴/8턴 AC 손실 해석)
echo ============================================================

echo.
echo [Step 1] Geometry^;Winding 캡처 (4/6/8 턴 권선 배치 확인)
"%PYTHON%" figures\capture_slot_views.py
if errorlevel 1 (
    echo [경고] 캡처 실패 — 계속 진행
)

echo.
echo [Step 2] 4턴 AC 손실 맵 해석 (Hybrid + FullFEA)
echo   전류 격자: 0.1 / 172.5 / 345.0 / 517.5 / 690.0 A  (= 460A x 6/4 스케일)
echo   위상 격자: 0 / 18 / 36 / 54 / 72 / 90 deg
echo   속도 격자: 2000 / 4000 / 8000 / 16000 RPM
"%PYTHON%" run_kturn_pipeline.py ^
  --base-mot "D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot" ^
  --turns 4 ^
  --output-dir ".\kturn_results" ^
  --skip-gen ^
  --currents 0.1 172.5 345.0 517.5 690.0 ^
  --phases 0.0 18.0 36.0 54.0 72.0 90.0 ^
  --speeds 2000 4000 8000 16000 ^
  --proximity-models 3 1 ^
  --sessions 1
if errorlevel 1 echo [오류] 4턴 해석 실패

echo.
echo [Step 3] 8턴 AC 손실 맵 해석 (Hybrid + FullFEA)
echo   전류 격자: 0.1 / 86.25 / 172.5 / 258.75 / 345.0 A  (= 460A x 6/8 스케일)
"%PYTHON%" run_kturn_pipeline.py ^
  --base-mot "D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot" ^
  --turns 8 ^
  --output-dir ".\kturn_results" ^
  --skip-gen ^
  --currents 0.1 86.25 172.5 258.75 345.0 ^
  --phases 0.0 18.0 36.0 54.0 72.0 90.0 ^
  --speeds 2000 4000 8000 16000 ^
  --proximity-models 3 1 ^
  --sessions 1
if errorlevel 1 echo [오류] 8턴 해석 실패

echo.
echo ============================================================
echo  완료! kturn_results\ 에 JSON 저장됨
echo ============================================================
pause
