function updatedTable = addCategoryVar2Table(inputTable, newVarName, newVarValues)
    % addCategoricalVariableToTable - 테이블에 새로운 카테고리형 변수를 추가합니다.
    %
    % Syntax: updatedTable = addCategoricalVariableToTable(inputTable, newVarName, newVarValues)
    %
    % Inputs:
    %   inputTable - 카테고리형 변수를 추가할 원본 테이블
    %   newVarName - 추가할 카테고리형 변수의 이름 (문자열)
    %   newVarValues - 카테고리형 변수에 할당할 값들 (셀 배열 또는 배열)
    %
    % Outputs:
    %   updatedTable - 수정된 테이블 (새로운 카테고리형 변수가 추가됨)

    % 입력된 값들을 카테고리형 데이터로 변환
    newCategoricalVar = categorical(newVarValues);
    
    % 새로운 카테고리형 변수를 테이블에 추가
    updatedTable = [inputTable, table(newCategoricalVar, 'VariableNames', {newVarName})];
end