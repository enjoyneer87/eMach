function summaryTable = extractStructSummary(data, pathPrefix, depth)
    % 초기 호출 시 pathPrefix는 빈 문자열, depth는 0이어야 합니다.
    if nargin < 2, pathPrefix = ''; end
    if nargin < 3, depth = 0; end  % 계층의 깊이 초기화
    
    % 결과를 저장할 테이블 초기화
    if isempty(pathPrefix)
        summaryTable = table('Size', [0, 5], 'VariableTypes', {'string', 'string', 'string', 'double', 'string'}, ...
            'VariableNames', {'Name', 'Hierarchy', 'Class', 'Depth', 'Size'});
    else
        summaryTable = table();
    end
    
    % 데이터 유형에 따라 처리
    if isstruct(data)
        % 구조체의 경우: 모든 필드를 순회
        fieldNames = fieldnames(data);
        for i = 1:length(fieldNames)
            fieldName = fieldNames{i};
            fieldValue = data.(fieldName);
            currentPath = fullfile(pathPrefix, fieldName); % 계층 구조 갱신
            dataSize = size(fieldValue); % 데이터 크기
            dataSizeStr = mat2str(dataSize); % 크기를 문자열로 변환
            
            % 현재 필드에 대한 정보 추가
            newRow = table(string(fieldName), string(currentPath), string(class(fieldValue)), ...
                depth + 1, string(dataSizeStr), ...
                'VariableNames', {'Name', 'Hierarchy', 'Class', 'Depth', 'Size'});
            summaryTable = [summaryTable; newRow];
            
            % 재귀 호출로 하위 필드 탐색
            if isstruct(fieldValue) || iscell(fieldValue)
                summaryTable = [summaryTable; extractStructSummary(fieldValue, currentPath, depth + 1)];
            end
        end
    elseif iscell(data)
        % 셀 배열의 경우: 모든 셀을 순회
        for i = 1:numel(data)
            cellValue = data{i};
            currentPath = sprintf('%s{%d}', pathPrefix, i); % 셀 인덱스로 계층 구조 갱신
            dataSize = size(cellValue); % 데이터 크기
            dataSizeStr = mat2str(dataSize); % 크기를 문자열로 변환
            
            % 재귀 호출로 셀 내용 탐색 (셀 자체에 대한 행은 추가하지 않음)
            summaryTable = [summaryTable; extractStructSummary(cellValue, currentPath, depth + 1)];
        end
    end
end

