function [motFileList,matFileListStr] = getResultMotMatList(parentPath)
    matFileList=findMatFiles(parentPath)';
    motFileList=findMOTFiles(parentPath)';
    NotAutosaveMotFileList=~contains(motFileList,'AutoSave');
    motFileList=motFileList(NotAutosaveMotFileList);
    DriveCycleMatFileChecker=contains(matFileList,'drive');
    DutyCycleMatFileList=matFileList(DriveCycleMatFileChecker);
    ElecMatFileChecker=contains(matFileList,'elecdata');
    ElecMatFileList=matFileList(ElecMatFileChecker);
    satuMatFileChecker=contains(matFileList,'Satu','IgnoreCase', true);
    satuMatFileList=matFileList(satuMatFileChecker);

    %%
    matFileListStr.satuMatFileList=satuMatFileList;
    matFileListStr.DutyCycleMatFileList=DutyCycleMatFileList;
    matFileListStr.ElecMatFileList=ElecMatFileList;

end