Dim answer
answer = MsgBox("Motor-CAD 슬롯 단면 캡처를 실행합니다." & vbCrLf & vbCrLf & _
    "4턴 캡처: 완료" & vbCrLf & _
    "6턴 캡처: 필요" & vbCrLf & _
    "8턴 캡처: 필요 (도체 높이 클램핑 검증)" & vbCrLf & vbCrLf & _
    "지금 6턴/8턴 캡처를 실행하시겠습니까?", _
    vbYesNo + vbQuestion, "Motor-CAD Slot Capture")

If answer = vbYes Then
    Dim pyExe, script, cmd
    pyExe = "C:\Users\user\.ansys_python_venvs\pyMotorEnv_310\Scripts\python.exe"
    script = "D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\figures\capture_slot_views.py"

    Dim wsh
    Set wsh = CreateObject("WScript.Shell")
    wsh.Run Chr(34) & pyExe & Chr(34) & " " & Chr(34) & script & Chr(34), 1, True
    MsgBox "캡처 완료! figures 폴더를 확인하세요.", vbInformation, "완료"
Else
    MsgBox "취소되었습니다. MATLAB에서 >> run_capture_slots 로 실행하세요.", vbInformation, "안내"
End If
