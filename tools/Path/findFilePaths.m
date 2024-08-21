function fullPathList = findFilePaths(fileList,baseDir)
    % if numel(fileList)==1
    if nargin<2
    curmFilePath=mfilename("fullpath");
    % curmFilePath='Z:\01_Codes_Projects\git_fork_emach\tools\Path\findFilePaths.m'
    [baseDir,~,~]=fileparts(curmFilePath);
    [baseDir,~,~]=fileparts(baseDir);
    end
    if ischar(fileList)
    fileList={fileList};
    end
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
            % if strcmp([name,ext], fileList{i})
            if strcmp([name], fileList{i})
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