function magnetTable = extractMagnetPositions(inputString,TargetString)
    % Split the input string by semicolons to separate individual entries
    entries = strsplit(inputString, ';');
    
    % Initialize arrays to store extracted data
    TargetStringNames = {};
    xPosValues = [];
    yPosValues = [];
    
    % Iterate through each entry
    for i = 1:numel(entries)
        entry = entries{i};
        % Check if the entry contains "Name:Magnet"
        if contains(entry, TargetString)
            % Extract Name, xPos, and yPos using regular expressions
            nameMatch = regexp(entry, 'Name:([^$]+)', 'tokens');
            xPosMatch = regexp(entry, 'XPos:([^$]+)', 'tokens');
            yPosMatch = regexp(entry, 'YPos:([^$]+)', 'tokens');
            
            if ~isempty(nameMatch) && ~isempty(xPosMatch) && ~isempty(yPosMatch)
                % Extract values from the matches
                TargetName = nameMatch{1}{1};
                xPos = str2double(xPosMatch{1}{1});
                yPos = str2double(yPosMatch{1}{1});
                
                % Append values to the arrays
                TargetStringNames{end+1} = TargetName;
                xPosValues(end+1) = xPos;
                yPosValues(end+1) = yPos;
            end
        end
    end
    
    % Create a table from the extracted data
    magnetTable = table(TargetStringNames', xPosValues', yPosValues', ...
        'VariableNames', {'TargetString', 'XPos', 'YPos'});
end
