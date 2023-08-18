% function DOETable = varStructToDOETable(varargin)
%     % Initialize an empty table to store the final result
%     DOETable = table();
% 
%     % Process each input struct and split the merged table
%     for i = 1:nargin
%         % Convert the current input struct to a table
%         variableTable = struct2table(varargin{i});
% 
%         % Split the merged variables into separate columns
%         variableTable = splitMergedTable(variableTable);
% 
%         % Horizontally concatenate the current table with the DOETable
%         if isempty(DOETable)
%             DOETable = variableTable;
%         else
%             % Check if the number of rows match before concatenating
%             if size(DOETable, 1) == size(variableTable, 1)
%                 DOETable = horzcat(DOETable, variableTable);
%             else
%                 error('Number of rows in tables do not match. Cannot concatenate.');
%             end
%         end
%     end
% end
% 
function sampleTable = convertVarStruct2DOETable(varargin)
    % Initialize an empty table to store the final result
    sampleTable = table();

    % Process each input struct and split the merged table
    for i = 1:nargin
        % Convert the current input struct to a table
        variableTable = struct2table(varargin{i});
        
        % Split the merged variables into separate columns
        variableTable = splitMergedTable(variableTable);
        
        % Check for duplicate variable names and remove them from variableTable
        [~, idxToRemove] = intersect(sampleTable.Properties.VariableNames, variableTable.Properties.VariableNames);
        variableTable(:, idxToRemove) = [];
        
        % Horizontally concatenate the current table with the DOETable
        if isempty(sampleTable)
            sampleTable = variableTable;
        else
            % Check if the number of rows match before concatenating
            if size(sampleTable, 1) == size(variableTable, 1)
                sampleTable = horzcat(sampleTable, variableTable);
            else
                error('Number of rows in tables do not match. Cannot concatenate.');
            end
        end
    end
end


