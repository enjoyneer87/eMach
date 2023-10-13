function MotFileList = removeAutoSaveFiles(MotFileList)
    % AutoSave 제외
    indicesToDelete = false(size(MotFileList));

    % ||contains(MotFileList{MotFileIndex}, 'MCAD')||
    for MotFileIndex = 1:numel(MotFileList)
        if contains(MotFileList{MotFileIndex}, 'AutoSave')||contains(MotFileList{MotFileIndex}, 'NotBuild')
            indicesToDelete(MotFileIndex) = true;
        end
    end

    MotFileList(indicesToDelete) = [];
    MotFileList = MotFileList';
end
