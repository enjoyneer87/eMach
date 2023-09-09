function modifiedTable = filterAndSortVarTablebyNameCell(originalTable, NameCell)
    % originalTable에서 LabLinkFormat에 있는 변수만 남기고 변수 순서를 LabLinkFormat에 맞게 정렬
    
    % 변수 이름 가져오기
    varNames = originalTable.Properties.VariableNames;
    
    % LabLinkFormat에 있는 변수만 선택하고 originalTable에 존재하는 변수만 남김
    varToKeep = intersect(varNames, NameCell);
    filteredTable = originalTable(:, varToKeep);
    
    % LabLinkFormat의 순서대로 변수 순서 정렬 (originalTable에 존재하는 변수만 고려)
    [~, idx] = ismember(NameCell, varNames);
    idx = idx(idx > 0); % originalTable에 존재하는 변수만 선택
    
    % 변수 순서 정렬을 위해 무시할 변수를 제외한 LabLinkFormat 변수만 선택
    LabLinkFormatToMove = NameCell(ismember(NameCell, varNames));
    
    % 변수 순서 정렬
    modifiedTable = movevars(filteredTable, LabLinkFormatToMove, 'After', varNames{end});
end