function filteredTable = filterMCADAutomationNameTable(MCADTable, filterCriteria,findType)
    if nargin>2
        checkType=checkfindType(findType);
    else
        checkType=0;
    end
    
    matchingIndices=[];
    % Find matching indices for the given filterCriteria
    if iscell(filterCriteria)
        for i=1:numel(filterCriteria)
        newMatchIndex = findMatchingIndex(MCADTable.AutomationName, filterCriteria{i},checkType);
        matchingIndices =[matchingIndices newMatchIndex];
        matchingIndices = unique(matchingIndices);
        end
    else
    matchingIndices = findMatchingIndex(MCADTable.AutomationName, filterCriteria,checkType);
    end
    % Filter the table using the matching indices
    filteredTable = MCADTable(matchingIndices, "AutomationName");
end