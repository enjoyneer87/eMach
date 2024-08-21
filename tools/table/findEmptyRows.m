function emptyRows = findEmptyRows(table, variableName)
    % findEmptyRows - 테이블의 특정 변수에서 비어 있는 행을 찾는 함수
    %
    % Syntax: emptyRows = findEmptyRows(table, variableName)
    %
    % Inputs:
    %   table - 테이블 데이터
    %   variableName - 변수를 나타내는 문자열 (예: 'VariableName')
    %
    % Outputs:
    %   emptyRows - 비어 있는 행의 논리적 인덱스 배열
    
    % 테이블의 해당 변수 값 가져오기
    data = table.(variableName);
    
    % 데이터 타입에 따라 비어 있는 값을 확인
    if isnumeric(data) || islogical(data)
        % 숫자형 또는 논리형의 경우 NaN 값이 비어 있는 값으로 간주
        emptyRows = isnan(data);
    elseif iscell(data)
        % 셀 배열의 경우, 빈 셀 또는 빈 문자열을 비어 있는 값으로 간주
        emptyRows = cellfun(@isempty, data);
    elseif ischar(data)
        % 문자열형의 경우, 빈 문자열을 비어 있는 값으로 간주
        emptyRows = strcmp(data, '');
    elseif isstring(data)
        % String 형의 경우, ""를 비어 있는 값으로 간주
        emptyRows = data == "";
    else
        error('지원되지 않는 데이터 유형입니다.');
    end
end