function InputTable = replaceSpacesWithUnderscores(InputTable)
    oldVarNames = InputTable.Properties.VariableNames;
    newVarNames = strrep(oldVarNames, ' ', '_');
    InputTable.Properties.VariableNames = newVarNames;
end