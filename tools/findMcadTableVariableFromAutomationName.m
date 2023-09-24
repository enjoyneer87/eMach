function currentValue = findMcadTableVariableFromAutomationName(McadVariableTable, AutomationName)
% from updateMcadTableVariable
    idx = strcmp(McadVariableTable.AutomationName, AutomationName);
    currentValue = McadVariableTable.CurrentValue(idx);
end