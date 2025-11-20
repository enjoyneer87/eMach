function T_out = expandNestedTableVariable(T_in, nestedVarName)
% T_in          : 입력 테이블 (예: 480행)
% nestedVarName : 테이블 내에서 확장할 변수 이름 (string or char)
% T_out         : 확장된 테이블 (예: 480 * 30 = 14400행)

    % 행 수
    numRows = height(T_in);

    % Nested 테이블을 포함하는 열 추출
    nestedTables = T_in.(nestedVarName);

    % 확장될 테이블 초기화
    expandedTables = cell(numRows, 1);

    for i = 1:numRows
        nested = nestedTables{i};  % 30행짜리 테이블

        % 나머지 변수들의 현재 i번째 값 가져오기
        baseRow = T_in(i, :);
        baseRow.(nestedVarName) = [];  % nested 열은 제외

        % 해당 행의 값 30번 반복
        baseRep = repmat(baseRow, height(nested), 1);

        % 붙이기
        expandedTables{i} = [baseRep, nested];
    end

    % 전체 병합
    T_out = vertcat(expandedTables{:});
end
