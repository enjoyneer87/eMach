function creationDate=getFileCreationDate(MotFilePath)

% 날짜 형식 지정 (예: 연-월-일)
dateFormat = "dd-MM-yyyy HH:mm:ss";

% PowerShell 명령어 구성, 날짜 형식을 적용
command = sprintf('powershell -command "(Get-Item ''%s'').CreationTime.ToString(''%s'')"', MotFilePath, dateFormat);

% 시스템 명령어 실행
[status, creationDate] = system(command);
end