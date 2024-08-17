function mkSubFolderFromFileList(directory,targetDir)
    folderNameList=findFolderNames(directory);
    newSubFolderPath = createSubFolderList(folderNameList, targetDir);
    for folderIndex=1:length(newSubFolderPath)
    folderName=newSubFolderPath{folderIndex};    
        if ~isfolder(folderName)
            mkdir(folderName)
        end
    end
end