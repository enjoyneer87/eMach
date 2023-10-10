function clearWithExclusion(excludeStr)
    % clearWithExclusion Clear all variables from the workspace excluding variables starting with the given string
    %
    % USAGE:
    %   clearWithExclusion('excludeVar');
    %
    % INPUT:
    %   excludeStr - String, prefix of variables to be kept in the workspace.

    % Convert excludeStr to regular expression
    excludePattern = ['^' excludeStr];

    % Get list of variables in the workspace
    allVars = evalin('base', 'who');
    
    % Find variable names that match the exclusion pattern
    varsToKeep = allVars(cellfun(@(x) ~isempty(regexp(x, excludePattern, 'once')), allVars));

    % Convert varsToKeep to a comma-separated list
    keepList = sprintf('%s,', varsToKeep{:});
    if ~isempty(keepList)
        keepList(end) = []; % Remove the trailing comma
    end

    % Clear all but the varsToKeep
    evalin('base', ['clearvars -except ' keepList]);
end
