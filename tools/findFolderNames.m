function folederNames = findFolderNames(directory)
    % 디렉토리 내의 모든 파일 목록을 얻어옴
    files = dir(directory);
    
    % MOT 파일을 저장할 셀 배열 초기화
    folederNames = {};
    
    % 디렉토리의 모든 파일에 대해서 반복
    for i = 1:length(files)
        file = files(i);
        
        % 현재 항목이 디렉토리인지 확인
        if file.isdir
            % "."과 ".." 디렉토리는 건너뜀
            if strcmp(file.name, '.') || strcmp(file.name, '..')
                continue;
            end
            
            % % 하위 디렉토리에 대해 재귀적으로 MOT 파일을 찾음
            % subDir = fullfile(directory, file.name);
            % subMOTFiles = findMOTFiles(subDir);
            [~, newfolderNames,] = fileparts(file.name);

            % 하위 디렉토리에서 찾은 MOT 파일들을 현재 리스트에 추가
            folederNames = [folederNames, newfolderNames];
            
        % else
        %     % 파일의 확장자가 ".mot"인지 확인하여 MOT 파일인지 판별
        %     [~, ~, ext] = fileparts(file.name);
        %     if strcmpi(ext, '.mot')
        %         % MOT 파일인 경우 경로를 리스트에 추가
        %         folederNames = [folederNames, fullfile(directory, file.name)];
        %     end
        end
    end
end
