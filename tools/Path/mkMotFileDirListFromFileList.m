function MotFileDirList=mkSubFolderFromFileList(FileList,targetDir)

    folderNameList=fieldnames(FileList.DOE);
    newSubFolderPath = createSubFolderList(folderNameList, targetDir);
    for folderIndex=1:length(newSubFolderPath)
    folderName=newSubFolderPath{folderIndex};    
        if ~isfolder(folderName)
            mkdir(folderName)
        end
    end
end