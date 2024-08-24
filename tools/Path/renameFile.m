function renameFile(oldFileName, newFileName)
    % renameFile: 지정된 디렉토리에서 파일 이름을 찾아 새 파일 이름으로 바꿈.
    %
    % 입력:
    %   directoryPath: 파일이 위치한 디렉토리 경로 (문자열)
    %   oldFileName: 기존 파일 이름 (문자열)
    %   newFileName: 새 파일 이름 (문자열)
    %
    % 예시:
    %   renameFile('C:\Documents', 'oldFile.txt', 'newFile.txt')
    
    % 기존 파일의 전체 경로 생성
    oldFilePath =findFilePaths(oldFileName);
    % newFilePath =findFilePaths(newFileName);
    oldFilePath =oldFilePath{1};
    newFilePath =strrep(oldFilePath,oldFileName,newFileName);
    % 파일이 존재하는지 확인
    if isfile(oldFilePath)
        % 파일 이름 변경
        movefile(oldFilePath, newFilePath);
        fprintf('File renamed from %s to %s\n', oldFileName, newFileName);
    else
        % 파일이 존재하지 않는 경우 경고 메시지 출력
        warning('The file %s does not exist in the directory %s.', oldFileName, directoryPath);
    end
end