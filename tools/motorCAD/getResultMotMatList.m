function [motFileList,matFileListStr] = getResultMotMatList(parentPath)

    %% Mot파일 분류
    motFileList                     =findMOTFiles(parentPath)';    
    NotAutosaveMotFileList          =~contains(motFileList,'AutoSave');
    motFileList                     =motFileList(NotAutosaveMotFileList);
    
    %% Mat파일 분류
    matFileList                     =findMatFiles(parentPath)';
    DriveCycleMatFileChecker        =contains(matFileList,'drive');
    DutyCycleMatFileList            =matFileList(DriveCycleMatFileChecker);
    ElecMatFileChecker              =contains(matFileList,'elecdata');
    ElecMatFileList                 =matFileList(ElecMatFileChecker);
    satuMatFileChecker              =contains(matFileList,'Satu','IgnoreCase', true);
    satuMatFileList                 =matFileList(satuMatFileChecker);

    %% Mat파일 분류후 구조체 저장
    matFileListStr.satuMatFileList      =satuMatFileList;
    matFileListStr.DutyCycleMatFileList =DutyCycleMatFileList;
    matFileListStr.ElecMatFileList      =ElecMatFileList;
end