function matchedFiles = checkDependencyInSubfolders(searchStr)
    % 현재 작업 폴더 확인
    topDir = pwd;
    
    % MATLAB의 현재 경로에 설정된 모든 경로를 가져오기
    pathStr = path;
    pathList = strsplit(pathStr, pathsep);
    
    % 현재 작업 폴더의 하위 폴더 찾기
    subfolders = dir(topDir);
    subfolders = subfolders([subfolders.isdir]); % 디렉토리만 선택
    subfolders = subfolders(~ismember({subfolders.name}, {'.', '..'})); % '.'와 '..' 제외

    % 결과를 저장할 빈 셀 배열 생성
    matchedFiles = {};

    % 각 하위 폴더를 순회하며, MATLAB 경로에 포함된 폴더인지 확인
    for j = 1:length(subfolders)
        subfolderPath = fullfile(topDir, subfolders(j).name);
        
        % MATLAB 경로에 이 하위 폴더가 포함되어 있는지 확인
        if any(startsWith(pathList, subfolderPath))
            % 하위 폴더를 포함한 모든 파일 검색
            fileList = dir(fullfile(subfolderPath, '**', '*.m'));
            
            % 각 파일을 순회하며 검색 문자열이 포함되어 있는지 확인
            for i = 1:length(fileList)
                % 파일 경로 생성
                filepath = fullfile(fileList(i).folder, fileList(i).name);
                
                % 파일 열기
                fid = fopen(filepath, 'r');
                
                if fid == -1
                    continue; % 파일을 열 수 없는 경우 건너뜀
                end
                
                % 파일 내용 읽기
                fileContent = fread(fid, '*char')';
                
                % 파일 닫기
                fclose(fid);
                
                % 검색 문자열이 파일 내용에 포함되어 있는지 확인
                if contains(fileContent, searchStr, "IgnoreCase", true)
                    % 포함되어 있다면 파일 이름을 리스트에 추가
                    matchedFiles{end+1} = filepath; % 파일의 전체 경로 추가
                end
            end
        end
    end
    
    % 결과 출력
    disp(matchedFiles);
end