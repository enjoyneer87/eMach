function mergedTable = mergeTablesAndMatchVariableTypes(table1, table2)
    % 테이블 크기 확인
    [rows1, cols1] = size(table1);
    [rows2, cols2] = size(table2);
    
    % 변수 이름 추출
    varNames1 = table1.Properties.VariableNames;
    varNames2 = table2.Properties.VariableNames;
    
    % 공통 변수 이름 찾기
    commonVarNames = intersect(varNames1, varNames2);
    
    % 공통 변수가 없을 경우 처리
    if isempty(commonVarNames)
        error('공통 변수가 없습니다.');
    end
    
    % 중복 변수 이름 처리 및 변수 형태 맞추기
    mergedTable = table;
    for i = 1:length(commonVarNames)
        varName = commonVarNames{i};
        varType1 = class(table1.(varName));
        varType2 = class(table2.(varName));
        
        if ~strcmp(varType1, varType2)
            if isnumeric(table1.(varName))
                table1.(varName) = num2cell(table1.(varName));
            elseif isnumeric(table2.(varName))
                table2.(varName) = num2cell(table2.(varName));
            elseif iscell(table1.(varName))
                table1.(varName) = cellfun(@num2str, table1.(varName), 'UniformOutput', false);
            elseif iscell(table2.(varName))
                table2.(varName) = cellfun(@num2str, table2.(varName), 'UniformOutput', false);
            end
        end
        
        mergedTable.(varName) = [table1.(varName); table2.(varName)];
    end
    
    % 나머지 변수 합치기
    remainingVars1 = setdiff(varNames1, commonVarNames);
    remainingVars2 = setdiff(varNames2, commonVarNames);
    
    for i = 1:length(remainingVars1)
        varName = remainingVars1{i};
        mergedTable.(varName) = table1.(varName);
    end
    
    for i = 1:length(remainingVars2)
        varName = remainingVars2{i};
        mergedTable.(varName) = table2.(varName);
    end
end

