function cleanedTable = removeIdenticalVariables(inputTable)
    % 입력 테이블의 변수 수와 행 수 얻기
    numVariables = size(inputTable, 2);
    numRows = size(inputTable, 1);
    
    % 각 변수에 대해 모든 행의 값을 비교하여 동일한 변수를 찾음
    identicalVariableIndices = [];
    for i = 1:numVariables
        variableData = inputTable{:, i};
        if all(variableData == variableData(1)) % 모든 값이 같으면
            identicalVariableIndices = [identicalVariableIndices, i]; % 동일한 변수로 표시
        end
    end
    
    % 동일한 변수를 삭제한 테이블 생성
    cleanedTable = inputTable;
    cleanedTable(:, identicalVariableIndices) = [];
end
