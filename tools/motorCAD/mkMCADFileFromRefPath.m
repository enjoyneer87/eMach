function NewMotFilePath= mkMCADFileFromRefPath(refModelPath,AddName)

[refModelDir,refModelMotFileName,FileExt]=fileparts(refModelPath);

NewMotFileDIR=fullfile(fileparts(refModelDir),AddName);
NewMotFileName=[refModelMotFileName,AddName];
NewMotFilePath=fullfile(NewMotFileDIR,[NewMotFileName,FileExt]);

% 폴더 생성
if ~isfolder(NewMotFileDIR)
    mkdir(NewMotFileDIR)
end

addpath(NewMotFileDIR)
%% 파일생성
checkFileNMove(NewMotFilePath)

if ~exist(NewMotFilePath)&&isfolder(NewMotFileDIR)
    copyfile(refModelPath,NewMotFilePath)
end

end