function MotFileDirList=mkMotFileDirListFromFileList(FileList,targetDir)
    folderNameList=fieldnames(FileList.DOE);
    MotFileDirList = createSubFolderList(folderNameList, targetDir);
    for folderIndex=1:length(MotFileDirList)
    folderName=MotFileDirList{folderIndex};    
        if ~isfolder(folderName)
            mkdir(folderName)
        end
    end
end