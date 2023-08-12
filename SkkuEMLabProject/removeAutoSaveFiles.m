function MotFileList = removeAutoSaveFiles(MotFileList)
    % AutoSave 제외
    indicesToDelete = false(size(MotFileList));

    for MotFileIndex = 1:numel(MotFileList)
        if contains(MotFileList{MotFileIndex}, 'AutoSave')
            indicesToDelete(MotFileIndex) = true;
        end
    end

    MotFileList(indicesToDelete) = [];
    MotFileList = MotFileList';
end
