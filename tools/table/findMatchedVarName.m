function containCell=findMatchedVarName(targetTable,findString)
    
    NameCell=targetTable.Properties.VariableNames;
    containIndex=contains(NameCell,findString);
    containCell=NameCell(containIndex);
    
end

