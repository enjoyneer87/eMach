function containCell=findMatchedVarName(targetTable,findString,~)
    if nargin>2
    findType='strcmp';
    else
    findType='contains';
    end

 
    NameCell=targetTable.Properties.VariableNames;

    if strcmp(findType,'contains')
    containIndex=contains(NameCell,findString);
    else
    containIndex=strcmp(NameCell,findString);
    end
    containCell=NameCell(containIndex);
    
    
end

