% 검색할 문자열
searchStr = 'copyPNGFilesToPNGFolder';

% 검색할 디렉토리 경로
topDir = 'Z:\01_Codes_Projects\git_fork_emach';

% 하위 폴더 및 파일 검색을 위한 함수 추가
addpath(fullfile(matlabroot, 'toolbox', 'matlab', 'general'));

% 하위 폴더를 포함한 모든 파일 검색
fileList = dir(fullfile(topDir, '**', '*.m'));

% 결과를 저장할 빈 셀 배열 생성
matchedFiles = {};

% 각 파일을 순회하며 검색 문자열이 포함되어 있는지 확인
for i = 1:length(fileList)
    
    % 파일 경로 생성
    filepath = fullfile(fileList(i).folder, fileList(i).name);
    
    % 파일 열기
    fid = fopen(filepath, 'r');
    
    % 파일 내용 읽기
    fileContent = fread(fid, '*char')';
    
    % 파일 닫기
    fclose(fid);
    
    % 검색 문자열이 파일 내용에 포함되어 있는지 확인
    if contains(fileContent, searchStr)
        
        % 포함되어 있다면 파일 이름을 리스트에 추가
        matchedFiles{end+1} = fileList(i).name;
        
    end
    
end

% 결과 출력
disp(matchedFiles);