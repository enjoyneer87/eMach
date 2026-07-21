@echo off
echo =====================================================
echo  Phase 2 Infill - Group 1 (16k/90deg reruns)
echo  4 points: 230/460/690/920A at 16000 RPM / 90deg
echo =====================================================

set PYTHON=C:\Users\user\.ansys_python_venvs\pyMotorEnv_310\Scripts\python.exe
set SCRIPT_DIR=%~dp0

cd /d "%SCRIPT_DIR%"

echo.
echo [1/4] 16000 RPM / 460.05 A / 90 deg (grid_hole)
"%PYTHON%" run_single_fea_point.py --speed 16000 --current 460.05 --phase 90
if errorlevel 1 goto :error

echo.
echo [2/4] 16000 RPM / 690.025 A / 90 deg (rerun_outlier)
"%PYTHON%" run_single_fea_point.py --speed 16000 --current 690.025 --phase 90
if errorlevel 1 goto :error

echo.
echo [3/4] 16000 RPM / 920.0 A / 90 deg (rerun_outlier - verify)
"%PYTHON%" run_single_fea_point.py --speed 16000 --current 920.0 --phase 90
if errorlevel 1 goto :error

echo.
echo [4/4] 16000 RPM / 230.075 A / 90 deg (rerun_outlier - verify)
"%PYTHON%" run_single_fea_point.py --speed 16000 --current 230.075 --phase 90
if errorlevel 1 goto :error

echo.
echo =====================================================
echo Done. Run JEET_AF_Pipeline.ipynb to refit AF model.
echo =====================================================
pause
goto :end

:error
echo ERROR on last step. Check Motor-CAD and .mot file.
pause

:end
