function filteredTable = filterMCADAutomationNameTable(MCADMagneticsTable, filterCriteria)
    
    % Find matching indices for the given filterCriteria
    matchingIndices = findMatchingIndex(MCADMagneticsTable.AutomationName, filterCriteria);
    
    % Filter the table using the matching indices
    filteredTable = MCADMagneticsTable(matchingIndices, "AutomationName");
end