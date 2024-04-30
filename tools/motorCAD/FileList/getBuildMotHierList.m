function FileList=getBuildMotHierList(FileList)
%% 7개 field를 가지는 구조체가 만들어집니다. mkDOEListWithHierarchy상호참조
   path=FileList.path;
    % allSubfolders = getAllSubfoldersRecursive(path);
            BuildMotFileNameList             =[];  
            BuildListMotFilePathList         =[];      
            BuildMotFileDirList              =[];  
   FileList.MotResultDirList                 =[];  
   FileList.MotResultLabDirList              =[]; 
   FileList.DOE                              =[];

%% 
    [BuildListMatPath,BuildList]=checkBuildList(path,1);  % check Saturation_Dat & CurrentMotFilePath &MotFileList(:,3)
  
    % BuildList = getBuildListFromMotFileList(FileList.MotFilePathList');
    % BuildList=makeNewBuildListWithCheckLabBuild(BuildList);
    BuildCheck = getBuildListResultFromBuildList(BuildList);
  

%% 

    for BuildListIndex=1:height(BuildCheck)
        if ~isempty(BuildCheck{BuildListIndex,1})
            BuildMotFileNameList{end+1}     = BuildCheck{BuildListIndex, 3};
            BuildListMotFilePathList{end+1} = BuildCheck{BuildListIndex, 5};
            BuildMotFileDirList{end+1}      = BuildCheck{BuildListIndex, 6};
        end
    % end
    % 
    % [motFileList,~,~,~]=getDriveMatList(FileList.path);
    % [MotFileDirList,fileNameList,~]=fileparts(motFileList);
    % 
    % MotNameIndex=contains(BuildMotFileNameList,fileNameList);
    % CheckMotFileList=motFileList(MotNameIndex);
    % if length(CheckMotFileList)==length(BuildListMotFilePathList)
            
    % FileList.BuildListMatPath           = BuildListMatPath';
    FileList.MotFileNameList            = BuildMotFileNameList';
    FileList.MotFilePathList            = BuildListMotFilePathList';
    FileList.MotFileDirList             = BuildMotFileDirList';
    FileList.MotResultDirList           = getMotResultDirFromMotFilePath(BuildListMotFilePathList)';
    FileList.MotResultLabDirList        = getMotResultLabDirFromMotFilePath(BuildListMotFilePathList)';
    FileList.DOE                        =createDOEstructFromMotFileList(BuildListMotFilePathList);
    % FileList.MotResultLabDirList=allSubfolders(LabFolderIndex);
    % else
        % error('Build안된게 포함되어있습니다')
    end
end