function newSubFolderPath = createHierarchy4SubFolder(folderNameList, targetDir)
    % Input validation
    if isempty(folderNameList) || isempty(targetDir)
        error('Both input arguments must be non-empty');
    end

    % Initialize the new subfolder path with the target directory
    newSubFolderPath = cell(1, length(folderNameList));

    % Initialize a temporary path with the target directory
    tempPath = targetDir;
    % Loop through the folder names to create the hierarchy
    for folderIndex = 1:length(folderNameList)
        tempPath = fullfile(tempPath, folderNameList{folderIndex});
        newSubFolderPath{folderIndex} = tempPath;
        
        % If you also want to physically create the folder (uncomment the following line)
        % if ~exist(tempPath, 'dir'), mkdir(tempPath); end
    end
end
