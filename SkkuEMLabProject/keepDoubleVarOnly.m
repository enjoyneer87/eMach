function filteredTable = keepDoubleVarOnly(inputTable)
    % Use varfun to check the data type of each variable in the input table
    dataTypeArray = varfun(@class, inputTable, 'OutputFormat', 'uniform');
    
    % Find the indices of variables with data type 'double'
    doubleVarIndices = find(strcmp(dataTypeArray, 'double'));
    
    % Filter the table to keep only the double data type variables
    filteredTable = inputTable(:, doubleVarIndices);
end
