function buildListMotFileDirName=getMotFileDirNameFromBuildList(BuildList,caseNum)   
    % motFileName, motFileDir 추출
    partsNameBuildList = strsplit(BuildList{caseNum, 2}, filesep);
    buildListMotFileDirName = partsNameBuildList{end - 1};
end