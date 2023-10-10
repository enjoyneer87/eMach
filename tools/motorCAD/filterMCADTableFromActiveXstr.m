function matchingTable = filterMCADTableFromActiveXstr(ActiveXParametersStruct, categoryName)
    % Load ActiveX parameters
    TableNames = fieldnames(ActiveXParametersStruct);
    idx = contains(TableNames, categoryName);
    fieldName = TableNames(idx);
    MCADTable = ActiveXParametersStruct.(fieldName{1});
    matchedTable=MCADTable;
    matchingTable = getTableMatchingRowsBetweenTwoTable(MCADTable, 'AutomationName', matchedTable, 'AutomationName');
end
