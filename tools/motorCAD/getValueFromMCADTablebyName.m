function value2Out = getValueFromMCADTablebyName(MCADTable,varargin)
    matchedTable=MCADTable;
    % Filter the table based on filterCriteria arguments
    for i = 1:numel(varargin)
        matchedTable = filterMCADAutomationNameTable(matchedTable, varargin{i});
    end
    % matchingTable=matchedTable
    matchingTable = getTableMatchingRowsBetweenTwoTable(MCADTable, 'AutomationName', matchedTable, 'AutomationName');

    if height(matchingTable)>1
        value2Out=struct();
        disp(['matching되는 value는 ', num2str(height(matchingTable)),'개라서 구조체로 저장됩니다']);
        for i=1:height(matchingTable)
            value2Out.(matchingTable.AutomationName{i})=convertCharTypeData2ArrayData(matchingTable.CurrentValue{i});
        end
    elseif height(matchingTable)==1
    disp(['matching되는 value의 이름은', matchingTable.AutomationName{1}]);
    value2Out=struct();
    value2Out.(matchingTable.AutomationName{1})=convertCharTypeData2ArrayData(matchingTable.CurrentValue{1});
    end
end