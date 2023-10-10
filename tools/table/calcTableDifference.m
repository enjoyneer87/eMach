function diffTable = calcTableDifference(table1, table2)
    % 두 테이블의 변수명을 가져옵니다.
    varNames = table1.Properties.VariableNames;
    
    % 새로운 테이블을 초기화합니다.
    diffTable = table();
    
    % 각 변수별로 값을 비교하고 차이를 계산하여 새로운 열을 만듭니다.
    for i = 1:length(varNames)
        varName = varNames{i};
        
        % 두 테이블의 동일한 변수를 가져옵니다.
        var1 = table1.(varName);
        var2 = table2.(varName);
        
        % 차이를 계산합니다.
        diff = var1 - var2;
        
        % 새로운 테이블에 차이 값을 추가합니다.
        diffTable.(varName) = diff;
    end
end
