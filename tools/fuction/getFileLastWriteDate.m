function LastWriteDate=getFileLastWriteDate(MotFilePath)

LastWriteDate={};
% 날짜 형식 지정 (예: 연-월-일)
dateFormat = "dd-MM-yyyy HH:mm:ss";


% PowerShell 명령 생성 (따옴표 이스케이프 처리)
command = sprintf('powershell -command "(Get-Item ''%s'').LastWriteTime.ToString(''%s'')"', MotFilePath, dateFormat);

% 시스템 명령 실행 및 결과 저장
[status, LastWriteDate] = system(command);

% 결과 출력
if status == 0
    fprintf('파일의 마지막 수정 날짜: %s\n', LastWriteDate);
else
    fprintf('명령 실행 실패: %s\n', LastWriteDate);
end

end



