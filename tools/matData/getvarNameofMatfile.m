function varNameCell=getvarNameofMatfile(matFilePath)
    
    matObj=matfile(matFilePath);
    varInfo = whos(matObj);
    varNameCell = {varInfo.name}';

end