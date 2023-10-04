function matchingTable = filterMCADTable(MCADTable, varargin)
    % Initialize filtered table with the original MCADTable
    filteredTable = MCADTable;

    % Apply each filter criteria
    for i = 1:numel(varargin)
        filteredTable = filterMCADAutomationNameTable(filteredTable, varargin{i});
    end

    matchingTable = getTableMatchingRowsBetweenTwoTable(MCADTable, 'AutomationName', filteredTable, 'AutomationName');

end
