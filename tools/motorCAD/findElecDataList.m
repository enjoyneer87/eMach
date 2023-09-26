function ElecMatFileList=findElecDataList(matFileList)
    ElecMatFileChecker=contains(matFileList,'elecdata');
    ElecMatFileList=matFileList(ElecMatFileChecker);
end