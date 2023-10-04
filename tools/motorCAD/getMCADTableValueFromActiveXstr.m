function matchingTable = getMCADTableValueFromActiveXstr(ActiveXStr, categoryName, mcad,varargin)
    % Load ActiveX parameters
    TableNames = fieldnames(ActiveXStr.ActiveXParametersStruct);
    idx = contains(TableNames, categoryName);
    fieldName = TableNames(idx);

    % Get MCAD Magnetics Table
    MCADTable = ActiveXStr.ActiveXParametersStruct.(fieldName{1});
    matchedTable=MCADTable;
    % Filter the table based on filterCriteria arguments
    for i = 1:numel(varargin)
        matchedTable = filterMCADAutomationNameTable(matchedTable, varargin{i});
    end

    % Get matching rows between MCADMagneticsTable and matchedTable
    matchingTable = getTableMatchingRowsBetweenTwoTable(MCADTable, 'AutomationName', matchedTable, 'AutomationName');
    matchingTable = getMcadTableVariable(matchingTable, mcad);
end