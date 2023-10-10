function MotResultDir=getMotResultDirFromMotFilePath(MotFilePath)
    % allSubfolders = getAllSubfoldersRecursive(FileList.path);
    [MotFileDirList,motFileNameList,~]=fileparts(MotFilePath);
    MotResultDir=fullfile(MotFileDirList,motFileNameList);
    % LabFolderIndex=contains(LastString,'Lab')
end