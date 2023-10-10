function importMatfile(filename, excludeStr)
    % loadWithExclusion Load .mat file excluding variables starting with the given string
    %
    % USAGE:
    %   loadedData = loadWithExclusion('data.mat', 'excludeVar');
    %
    % INPUTS:
    %   filename - String, name of the .mat file.
    %   excludeStr - String, prefix of variables to be excluded.
    %
    % OUTPUTS:
    %   loadedData - Structure, loaded data excluding specified variables.

    % Convert excludeStr to regular expression
    if nargin==2
        excludePattern = ['^(?!',excludeStr,')...'];      
        % Get list of variables in the .mat file
        fileInfo = whos('-file', filename);
        varNames = {fileInfo.name};    
        % Find variable names that do not match the exclusion pattern
        % includeVarNames = varNames(~cellfun(@(x) ~isempty(regexp(x, excludePattern, 'once')), varNames));   
        % Load specified variables from the .mat file
        % load(filename, includeVarNames{:});
        % load(filename,"-regexp","^(?!hwy)...")
        load(filename,"-regexp",excludePattern)

    else 
        % load(filename);
    end
end
