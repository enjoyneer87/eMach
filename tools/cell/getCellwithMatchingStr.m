function modifiedCell = getCellwithMatchingStr(originalCell, str2Contain)
    % Input validation
    if ~iscellstr(originalCell) || ~ischar(str2Contain)
        error('Both inputs must be cell arrays of strings or a string respectively.');
    end
    
    % Find the indices of matching strings
    matchingIndices = contains(originalCell, str2Contain,'IgnoreCase',true);
    
    % Remove those indices from the original cell
    modifiedCell = originalCell(matchingIndices);
end
