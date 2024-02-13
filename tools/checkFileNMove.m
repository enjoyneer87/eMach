function checkFileNMove(FilePath)

    if exist(FilePath, 'file') == 2
        % 백업 날짜와 시간을 문자열로 가져옵니다 (예: '20240211_1530' 형식).
        backupDateTime = datestr(now, 'yyyymmdd_HHMM');    
        % 파일 이름과 확장자를 분리합니다.
        [filePath, fileName, fileExt] = fileparts(FilePath);    
        % 새 파일 경로를 생성합니다. 날짜와 시간을 파일 이름 끝에 추가합니다.
        newFilePath = fullfile(filePath, [fileName, '_', backupDateTime, fileExt]);
        movefile(FilePath, newFilePath);
        % delete(FilePath)
        disp(['파일이 존재하여 백업하고 다시 생성하였습니다.',newFilePath]);
    end

end