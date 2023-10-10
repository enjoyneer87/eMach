function isVar = isvarofTable(tbl, varName)
    % isvarofTable Check if varName is a variable of the table tbl
    %
    % USAGE:
    %   isVar = isvarofTable(tbl, 'VariableName');
    %
    % INPUTS:
    %   tbl - Table, the input table.
    %   varName - String, the name of the variable to check.
    %
    % OUTPUT:
    %   isVar - Logical, true if varName is a variable of tbl, false otherwise.

    isVar = ismember(varName, tbl.Properties.VariableNames);
end
