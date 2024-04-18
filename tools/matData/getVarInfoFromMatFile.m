function varInfo=getVarInfoFromMatFile(matFilePath)    
    matObj  =matfile(matFilePath);
    varInfo = whos(matObj);
end