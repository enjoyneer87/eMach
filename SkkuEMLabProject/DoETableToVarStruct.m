function variable = DoETableToVarStruct(DoETable)
    % Initialize an empty table to store the final result
    variable = table();

    % Process each input struct and split the merged table
    for i = 1:nargin
        % Convert the current input struct to a table
        variableTable = struct2table(varargin{i});
        
        % Split the merged variables into separate columns
        variableTable = splitMergedTable(variableTable);
        
        % Check for duplicate variable names and remove them from variableTable
        [~, idxToRemove] = intersect(variable.Properties.VariableNames, variableTable.Properties.VariableNames);
        variableTable(:, idxToRemove) = [];
        
        % Horizontally concatenate the current table with the DOETable
        if isempty(variable)
            variable = variableTable;
        else
            % Check if the number of rows match before concatenating
            if size(variable, 1) == size(variableTable, 1)
                variable = horzcat(variable, variableTable);
            else
                error('Number of rows in tables do not match. Cannot concatenate.');
            end
        end
    end
end

