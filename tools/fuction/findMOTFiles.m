function motFiles = findMOTFiles(directory)
    % 빠르게 검색할 수 있도록 비재귀적이고 벡터화된 방식으로 디렉토리 트리를 탐색하여 .mot 파일 전체 경로를 반환합니다.
    % directory: 시작 디렉토리 (문자열)
    % motFiles: 셀 배열, 발견된 .mot 파일의 전체 경로
    
    % 입력 디렉토리 유효성 검사
    if nargin < 1 || isempty(directory)
        error('directory 입력이 필요합니다.');
    end
    if ~ischar(directory) && ~isstring(directory)
        error('directory는 문자열이어야 합니다.');
    end
    directory = char(directory);
    if ~isfolder(directory)
        error('지정된 경로가 존재하는 디렉토리가 아닙니다.');
    end

    % 스택(셀 배열) 초기화: 시작 디렉토리를 넣음
    stack = {directory};
    motFiles = {};
    
    % 루프를 사용한 비재귀적 탐색 (빠른 문자열 연결을 위해 cellcat을 최소화)
    while ~isempty(stack)
        % 스택에서 디렉토리 하나를 꺼냄
        current = stack{end};
        stack(end) = [];
        
        % 현재 디렉토리의 항목 조회 ('.' 및 '..' 자동 제외)
        d = dir(current);
        if isempty(d)
            continue;
        end
        
        % 분류: 디렉토리와 파일 분리 (벡터화)
        isdirFlags = [d.isdir];
        names = {d.name};
        
        % 하위디렉토리 처리(디렉토리 이름이 '.' 또는 '..'인 것은 제외)
        dirIdx = find(isdirFlags);
        if ~isempty(dirIdx)
            % 필터링하여 실제 하위 디렉토리만 스택에 추가
            for k = 1:numel(dirIdx)
                nm = names{dirIdx(k)};
                if strcmp(nm, '.') || strcmp(nm, '..')
                    continue;
                end
                stack{end+1} = fullfile(current, nm); %#ok<AGROW>
            end
        end
        
        % 파일 처리: 확장자가 .mot 인 파일만 선택
        fileIdx = find(~isdirFlags);
        if ~isempty(fileIdx)
            % 각 파일의 확장자 검사 (벡터화된 fileparts 대체)
            for k = 1:numel(fileIdx)
                nm = names{fileIdx(k)};
                [~, ~, ext] = fileparts(nm);
                if strcmpi(ext, '.mot')
                    motFiles{end+1} = fullfile(current, nm); %#ok<AGROW>
                end
            end
        end
    end
end