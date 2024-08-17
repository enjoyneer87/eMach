function fullPathList = findFilePaths(baseDir, fileList)
    % if numel(fileList)==1
        
    fullPathList = cell(size(fileList)); % Initialize the cell array for full paths

    % Get the list of all files in baseDir and its subdirectories
    allFiles = dir(fullfile(baseDir, '**', '*'));

    % Iterate over the file list
    for i = 1:length(fileList)
        found = false;
        for j = 1:length(allFiles)
            % Skip directories
            if allFiles(j).isdir
                continue;
            end
            
            % Check if the file name matches
            [~, name, ext] = fileparts(allFiles(j).name);
            if strcmp([name, ext], fileList{i})
                fullPathList{i} = fullfile(allFiles(j).folder, allFiles(j).name);
                found = true;
                break;
            end
        end
        
        % Warn if the file is not found
        if ~found
            warning('File %s not found in directory %s or its subdirectories.', fileList{i}, baseDir);
        end
    end
end