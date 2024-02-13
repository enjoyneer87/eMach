function matchingTable = getMCADTableValueFromActiveXstr(ActiveXParametersStruct, categoryName, mcad,varargin)
    % Load ActiveX parameters
    % ActiveXParametersStruct=ActiveXStr
    % categoryName='Winding'
    TableNames = fieldnames(ActiveXParametersStruct);
    idx = contains(TableNames, categoryName);
    fieldName = TableNames(idx);
    if length(fieldName)>1   
    disp('일치하는 catergory가 하나이상입니다')
    idx = strcmp(TableNames, categoryName);
    end
    fieldName = TableNames(idx);

    % Get MCAD Magnetics Table
    MCADTable = ActiveXParametersStruct.(fieldName{1});
    %%
    matchedTable=MCADTable;
    % Filter the table based on filterCriteria arguments
    for i = 1:numel(varargin)
        matchedTable = filterMCADAutomationNameTable(matchedTable, varargin{i});
    end

    % Get matching rows between MCADMagneticsTable and matchedTable
    matchingTable = getTableMatchingRowsBetweenTwoTable(MCADTable, 'AutomationName', matchedTable, 'AutomationName');
    matchingTable = getMcadTableVariable(matchingTable, mcad);
end