function mergedTable = mergeTables(table1, table2)
    % 테이블의 크기를 가져옴
    [table1Height, table1Width] = size(table1);
    [table2Height, table2Width] = size(table2);

    if table1Height == table2Height
        % 행이 같으면 변수명이 겹치는지 검사
        commonVars = intersect(table1.Properties.VariableNames, table2.Properties.VariableNames);
        if ~isempty(commonVars)
            % 겹치는 변수명이 있다면, table2의 변수명을 변경
            for varName = commonVars
                newName = ['same' varName{1}];
                table2.Properties.VariableNames{strcmp(table2.Properties.VariableNames, varName{1})} = newName;
            end
        end
        % 변수명을 수정한 후 테이블을 가로로 합침
        mergedTable = [table1, table2];
    elseif table1Width == table2Width && all(ismember(table1.Properties.VariableNames, table2.Properties.VariableNames))
        % 너비가 같고 모든 변수명이 같으면 세로로 합침
        mergedTable = vertcat(table1, table2);
    else
        error('테이블을 합칠 수 없습니다.');
    end
end
