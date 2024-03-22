function updatedTable = convertMcadTable2UnvTable(inputTable)
    % addUniformCategoricalVariable - 테이블에 새로운 카테고리형 변수를 추가하고, 모든 행을 동일한 카테고리 값으로 설정
    %
    % Syntax: updatedTable = addUniformCategoricalVariable(inputTable, newVarName, categoryList)
    %
    % Inputs:
    %   inputTable - 카테고리형 변수를 추가할 원본 테이블
    %   newVarName - 추가할 카테고리형 변수의 이름 (문자열)
    %   categoryList - 가능한 카테고리 값의 목록 (셀 배열), 이 중 첫 번째 값이 모든 행에 할당됨
    %
    % Outputs:
    %   updatedTable - 수정된 테이블 (새로운 카테고리형 변수 추가 및 값 설정)

    % 입력된 카테고리 목록의 첫 번째 값으로 모든 행을 일괄 설정

    newVarName='dataSWCategory';
    categoryList={'MCAD','JMAG','postCalc','MatlabInput','etc'};


    %%
    uniformValue = repmat({categoryList{1}}, height(inputTable), 1);
    
    % addCategoryVar2Table(inputTable,newVarName,categoryList)
    % 새로운 카테고리형 변수 생성 및 테이블에 추가
    newCategoricalVar = categorical(uniformValue, categoryList);
    updatedTable = [inputTable, table(newCategoricalVar, 'VariableNames', {newVarName})];
end
