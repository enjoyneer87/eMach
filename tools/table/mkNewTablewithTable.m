function newTable = mkNewTablewithTable(existTable, newVarNames, varargin)
    % mkNewTablewithTable - 기존 테이블의 변수 중 일부에 값을 지정하고
    % 나머지 변수는 빈 값으로 초기화하여 새로운 테이블을 생성하는 함수
    %
    % Syntax: newTable = mkNewTablewithTable(existTable, newVarNames, varargin)
    %
    % Inputs:
    %   existTable  - 기존 테이블
    %   newVarNames - 새로운 테이블 변수 이름 목록 (셀 배열)
    %   varargin    - 각 변수에 대응하는 값들 (순서대로 입력)
    %
    % Outputs:
    %   newTable - 생성된 새로운 테이블

    % 기존 테이블의 변수 이름과 개수 가져오기
    varNamesExist = existTable.Properties.VariableNames;
    numVarsExist = width(existTable);

    % 새로운 테이블 생성
    newTable = table();  % 빈 테이블 초기화
    
    for i = 1:numVarsExist
        varName = varNamesExist{i};
        if ismember(varName, newVarNames)
            % newVarNames에 있는 변수라면 해당 값 할당
            idx = find(strcmp(newVarNames, varName));
            % 입력받은 데이터를 셀 배열로 변환하여 할당
            newTable.(varName) = {varargin{idx}};
        else
            % 그렇지 않으면 빈 셀 배열로 초기화
            newTable.(varName) = cell(height(existTable), 1);
        end
    end
end
