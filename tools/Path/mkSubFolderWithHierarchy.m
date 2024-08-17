function mkSubFolderWithHierarchy(directory,targetDir)
    folderNameList=findFolderNames(directory);
    newSubFolderPath=makeSubFolderHierarchy(folderNameList,targetDir);
    for folderIndex=1:length(newSubFolderPath)
    folderName=newSubFolderPath{folderIndex};    
        if ~isfolder(folderName)
            mkdir(folderName)
        end
    end
end