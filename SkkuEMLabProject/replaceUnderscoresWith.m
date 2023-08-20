function InputTable = replaceUnderscoresWith(InputTable)
    if istable(InputTable)
    oldVarNames = InputTable.Properties.VariableNames;
    end
    oldVarNames = InputTable;
    newVarNames = strrep(oldVarNames, '_', ' ');
    InputTable = newVarNames;
  if istable(InputTable)
    InputTable.Properties.VariableNames = newVarNames;
  end
  end