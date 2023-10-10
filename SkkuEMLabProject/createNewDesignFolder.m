function newFolder = createNewDesignFolder(refMotFilePath, CaseNumber)
    % 새 폴더를 생성하는 함수
    % 입력:
    % - refMotFilePath: 참조 운동 파일의 경로
    % - CaseNumber: 새로운 폴더의 경우 번호
    % 출력:
    % - newFolder: 생성된 새 폴더의 경로
    if isfile(refMotFilePath)
    refMotFilePath=SatuMapFilePath;
    % refMotFilePath를 파일 경로 구분자(filesep)를 기준으로 분할
    parts = strsplit(refMotFilePath, filesep);
    
    % 부모 경로는 마지막 두 부분을 제외한 나머지 부분들을 합쳐서 생성
    parentPath = fullfile(parts{1:end-2});
    else isfolder(refMotFilePath)
    parentPath=refMotFilePath;
    end
    % refMotFilePath의 경로, 파일명, 확장자를 추출
    % [filepath, name, ext] = fileparts(refMotFilePath);
    
    % 새 폴더 경로 생성: 부모 경로 / 'DOE' / 파일명_Design_케이스번호
    newFolder = fullfile(parentPath, 'DOE', ['Design', sprintf('%04d', CaseNumber-1)]);
end
