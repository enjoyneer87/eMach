function filteredTable = replaceNaNofTable2Zero(filteredTable)
    VariableNamesCell = filteredTable.Properties.VariableNames;  % 모든 변수 이름을 가져옵니다.
    for k = 1:length(VariableNamesCell)
        filteredTable.(VariableNamesCell{k})(isnan(filteredTable.(VariableNamesCell{k}))) = 0;  % 각 변수에 대해 NaN 값을 0으로 설정합니다.
    end
end