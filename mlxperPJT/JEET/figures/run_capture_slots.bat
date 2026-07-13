@echo off
chcp 65001 > nul
echo === Motor-CAD Slot View Capture ===
echo.
"C:\Users\user\.ansys_python_venvs\pyMotorEnv_310\Scripts\python.exe" "%~dp0capture_slot_views.py"
echo.
echo === Done ===
pause
