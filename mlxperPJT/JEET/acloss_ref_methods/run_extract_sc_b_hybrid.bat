@echo off
echo =====================================================
echo  SC Hybrid MS B extraction (extract_sc_b_hybrid.py)
echo  venv: C:\Users\user\.ansys_python_venvs\pyMotorEnv_310
echo =====================================================

set SCRIPT_DIR=%~dp0
set PYTHON=C:\Users\user\.ansys_python_venvs\pyMotorEnv_310\Scripts\python.exe

cd /d "%SCRIPT_DIR%"

echo Running: %PYTHON% extract_sc_b_hybrid.py
echo.
"%PYTHON%" extract_sc_b_hybrid.py

echo.
echo =====================================================
echo Done. Check sc_b_data_hybrid/ for JSON output.
echo =====================================================
pause
