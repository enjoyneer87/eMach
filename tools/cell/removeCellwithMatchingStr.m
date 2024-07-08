function modifiedCell = removeCellwithMatchingStr(originalCell, strToRemove)
    % Input validation
    if ~iscellstr(originalCell) || ~ischar(strToRemove)
        error('Both inputs must be cell arrays of strings or a string respectively.');
    end
    
    % Find the indices of matching strings
    matchingIndices = contains(originalCell, strToRemove,"IgnoreCase",true);
    % matchingIndices = contains(originalCell, strToRemove);

    % Remove those indices from the original cell
    modifiedCell = originalCell(~matchingIndices);
end
