function tbl = replaceSpacesWithUnderscores(tbl)
    oldVarNames = tbl.Properties.VariableNames;
    newVarNames = strrep(oldVarNames, ' ', '_');
    tbl.Properties.VariableNames = newVarNames;
end