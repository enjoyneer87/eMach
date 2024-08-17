function sortedMagnetTables = sortMagnetTableByNumber(PartStructByType)
    % Initialize an empty structure to hold the sorted tables
    sortedMagnetTables = struct();
    
    % Get the number of rows in the MagnetTable
    numRows = height(PartStructByType.MagnetTable);
    
    % Iterate over each row in the MagnetTable
    for i = 1:numRows
        % Extract the current name
        currentName = PartStructByType.MagnetTable.Name{i};
        
        % Use regular expression to find the number after 'Magnet'
        matches = regexp(currentName, 'Magnet(\d+)', 'tokens');
        
        % Check if there is a match
        if ~isempty(matches)
            % Extract the number
            magnetNumber = str2double(matches{1}{1});
            
            % Create a new table if it does not exist
            if ~isfield(sortedMagnetTables, ['Magnet' num2str(magnetNumber)])
                sortedMagnetTables.(['Magnet' num2str(magnetNumber)]) = [];
            end
            
            % Append the current row to the corresponding table
            sortedMagnetTables.(['Magnet' num2str(magnetNumber)]) = ...
                [sortedMagnetTables.(['Magnet' num2str(magnetNumber)]); PartStructByType.MagnetTable(i, :)];
        end
    end
end
