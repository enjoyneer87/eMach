function currentValue = findMcadTableVariableFromAutomationName(McadVariableTable, AutomationName)
% from updateMcadTableVariable
    idx = contains(McadVariableTable.AutomationName, AutomationName);
    TypeofCurrentValue=class(McadVariableTable.CurrentValue);
    switch TypeofCurrentValue 
        case 'double'
        currentValue = McadVariableTable.CurrentValue(idx);
        case 'cell'
       
        currentValue = McadVariableTable.CurrentValue{idx};
    end
end