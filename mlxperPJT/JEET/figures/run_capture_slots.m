%% run_capture_slots.m
% Motor-CAD API 슬롯 단면 캡처 스크립트 실행 (MATLAB wrapper)
%
% 실행: >> run_capture_slots
% 결과: JEET/figures/ 에 slot_view_4turn.png, slot_view_6turn.png, slot_view_8turn.png 저장

pyEnv  = 'C:\Users\user\.ansys_python_venvs\pyMotorEnv_310\Scripts\python.exe';
script = fullfile(fileparts(mfilename('fullpath')), 'capture_slot_views.py');

cmd = sprintf('"%s" "%s"', pyEnv, script);
fprintf('Running: %s\n\n', cmd);

[status, output] = system(cmd);
disp(output);

if status == 0
    fprintf('[OK] 캡처 완료\n');
else
    fprintf('[ERROR] 종료코드 %d\n', status);
end
