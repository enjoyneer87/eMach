function FileList=createMotResultDirListFromMotFileList(FileList)

for DirIndex=1:length(FileList.MotFilePathList)
    MotFilePath=findMOTFiles(FileList.MotFilePathList{DirIndex});
    if length(MotFilePath)>1
        error('여러개의 MotFile이 한개의 MotFileDir안에 있습니다')
    elseif isempty(MotFilePath)
        error('MotFileDir안에 Mot파일이 없습니다')
    else 
        [~,MotResultDirName2Check,~]=fileparts(MotFilePath{1});
        if strcmp(FileList.MotFileNameList{DirIndex},MotResultDirName2Check)
            FileList.MotResultDirList{DirIndex}=fulfile(FileList.MotFileDirList{DirIndex},MotResultDirName2Check);
        end
    end
end