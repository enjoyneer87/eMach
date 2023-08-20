function deleteFiles(fileList)
    for i = 1:length(fileList)
        filename = fileList{i};
        
        if exist(filename, 'file') == 2
            delete(filename); % Delete the file
            disp(['Deleted: ', filename]);
        else
            disp(['File not found: ', filename]);
        end
    end
end