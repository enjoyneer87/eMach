function DutyCycleMatFileList=findDriveCycleDataList(matFileList)
    DriveCycleMatFileChecker=contains(matFileList,'drive');
    DutyCycleMatFileList=matFileList(DriveCycleMatFileChecker);
end