function FileList=createMotResultDirListFileList(FileList)
    for DirIndex=1:length(FileList.MotFileDirList)
        MotResultDir=fullfile(FileList.MotFileDirList{DirIndex},FileList.MotFileNameList{DirIndex});
        MotResultDirList{DirIndex}=MotResultDir;
    end
end
