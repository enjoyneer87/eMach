function FileList=getBuildMotHierList(FileList)
%% 7개 field를 가지는 구조체가 만들어집니다. mkDOEListWithHierarchy상호참조
path=FileList.path;
    % allSubfolders = getAllSubfoldersRecursive(path);
            BuildMotFileNameList             =[];  
            BuildListMotFilePathList         =[];      
            BuildMotFileDirList              =[];  
   FileList.BuildMotResultDirList            =[];  
   FileList.BuildMotResultLabDirList         =[]; 
   FileList.BuildDOE                         =[];

%% 
    [BuildListMatPath,BuildList]=checkBuildList(path,1);  % check Saturation_Dat & CurrentMotFilePath &MotFileList(:,3)
    BuildCheck = getBuildListResultFromBuildList(BuildList);
  
%% 

    for BuildListIndex=1:height(BuildCheck)
        if ~isempty(BuildCheck{BuildListIndex,1})
            BuildMotFileNameList{end+1}     = BuildCheck{BuildListIndex, 3};
            BuildListMotFilePathList{end+1} = BuildCheck{BuildListIndex, 5};
            BuildMotFileDirList{end+1}      = BuildCheck{BuildListIndex, 6};
        end
    end
    FileList.BuildListMatPath           = BuildListMatPath';
    FileList.BuildMotFileNameList       = BuildMotFileNameList';
    FileList.BuildListMotFilePathList   = BuildListMotFilePathList';
    FileList.BuildMotFileDirList        = BuildMotFileDirList';
    FileList.BuildMotResultDirList      = getMotResultDirFromMotFilePath(BuildListMotFilePathList)';
    FileList.BuildMotResultLabDirList   = getMotResultLabDirFromMotFilePath(BuildListMotFilePathList)';
    FileList.DOE                        =createDOEstructFromMotFileList(BuildListMotFilePathList);
    % FileList.MotResultLabDirList=allSubfolders(LabFolderIndex);

end