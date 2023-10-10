function mergedTable = mergeTables(table1, table2)
    [table1Height, table1Width] = size(table1);
    [table2Height, table2Width] = size(table2);

    if table1Height == table2Height
        % 행이 같으면 가로로 합침 (horzcat)
        mergedTable = [table1, table2];
    elseif table1Width == table2Width && all(ismember(table1.Properties.VariableNames, table2.Properties.VariableNames))
        % 너비가 같고 변수명도 같으면 세로로 합침 (vertcat)
        mergedTable = vertcat(table1, table2);
    else
        error('테이블을 합칠 수 없습니다.');
    end
end
