function MotResultLabDir=getMotResultLabDirFromMotFilePath(MotFilePath)
    MotResultDir=getMotResultDirFromMotFilePath(MotFilePath);
    MotResultLabDir=fullfile(MotResultDir,'Lab');
end