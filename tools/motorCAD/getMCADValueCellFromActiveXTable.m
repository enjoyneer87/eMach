function MCADValue=getMCADValueCellFromActiveXTable(MCADTable,AutomationName)
%% filterCriteris
filterCriteria=AutomationName;
matchingIndices = findMatchingIndex(MCADTable.AutomationName, filterCriteria);
%% data Out
MCADValue=MCADTable.CurrentValue(matchingIndices);

end