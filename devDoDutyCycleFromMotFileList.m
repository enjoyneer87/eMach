
DoDutyCycleFromMotFileList;

DoDutyCycleFromMotFileList(DOE8p48sVVScaledBuildPath)

motData=getDataFromMotFiles(BuildScaledMotFilePath);

i=1
    BuildScaledMotFilePath=readMotFileList{i};

    if isfile(BuildScaledMotFilePath)    
    mcad(spmdIndex).LoadFromFile(BuildScaledMotFilePath)
    end