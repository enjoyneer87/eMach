function moveFilesToSubfolder(fileList, targetSubfolder)
    % Check if the target subfolder exists, if not, create it
    if ~exist(targetSubfolder, 'dir')
        mkdir(targetSubfolder);
    end
    
    % Iterate over the file list
    for i = 1:length(fileList)
        
        [filePath, fileName, fileExt] = fileparts(fileList{i});
        
        % Check if the file is already in the target subfolder
        if ~contains(filePath, targetSubfolder)
            % Construct the source and destination paths
            sourcePath = fullfile(filePath, [fileName, fileExt]);
            destinationPath = fullfile(targetSubfolder, [fileName, fileExt]);
            
            % Move the file to the target subfolder
            movefile(sourcePath, destinationPath);
            fprintf('Moved %s to %s\n', sourcePath, destinationPath);
        end
    end
end
