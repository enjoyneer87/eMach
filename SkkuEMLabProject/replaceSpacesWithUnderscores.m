function InputTable = replaceSpacesWithUnderscores(InputTable)
    
    if istable(InputTable)
    oldVarNames = InputTable.Properties.VariableNames;
    newVarNames = strrep(oldVarNames, ' ', '_');
    InputTable.Properties.VariableNames = newVarNames;
    else
    oldVarNames=InputTable;
    newVarNames = strrep(oldVarNames, ' ', '_');
    InputTable=newVarNames;
    end
end