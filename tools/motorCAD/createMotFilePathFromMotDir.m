function MotFilePathList=createMotFilePathFromMotDir(MotFileDirList)
    for motIndex=1:length(MotFileDirList)
        [~,MotFileNameList{motIndex},~]=fileparts(MotFileDirList{motIndex});
        MotFilePathList{motIndex}      = fullfile(MotFileDirList{motIndex}, [MotFileNameList{motIndex},'.mot']);
    end    
end