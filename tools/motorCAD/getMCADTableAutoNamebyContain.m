function [AutomationName,rowIdx]=getMCADTableAutoNamebyContain(McadVariableTable,Name2Find)
    rowIdx = find(contains(McadVariableTable.AutomationName, Name2Find,IgnoreCase=true));   
    if ~isempty(rowIdx)&len(rowIdx)<2
     AutomationName=McadVariableTable.AutomationName{rowIdx};
    elseif len(rowIdx)==0
    disp('해당되는 이름이 없습니다')
    else
     AutomationName=McadVariableTable.AutomationName(rowIdx);
    end    
end