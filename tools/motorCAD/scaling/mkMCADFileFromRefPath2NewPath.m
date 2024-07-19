function mkMCADFileFromRefPath2NewPath(refModelPath,AddName,additionalOption,NewParentPath)

[refModelDir,refModelMotFileName,FileExt]=fileparts(refModelPath);    


[~,LastStr,~]=fileparts(refModelDir);

%NewMotFileDIR 폴더 생성

NewMotFileDIR=fullfile(NewParentPath,[AddName,LastStr]);
if ~isfolder(NewMotFileDIR)
    mkdir(NewMotFileDIR);
end    


%% NewMotFile 
NewMotFileName=refModelMotFileName;
    if nargin>2
    NewMotFilePath=fullfile(NewMotFileDIR,[NewMotFileName,additionalOption,FileExt]);
    else
    NewMotFilePath=fullfile(NewMotFileDIR,[NewMotFileName,FileExt]);
    end

% NewMotFile 의  Lab Folder Dir
NewMotFileLabDir=fullfile(NewMotFileDIR,[NewMotFileName,'\Lab']);
%% 파일생성 CheckN Move 할때도 Lab 폴더 있는지 확인하고 생성
if ~isfolder(NewMotFileLabDir)
checkFileNMove(NewMotFilePath)    
end

%% 파일복사 중복 처리
if ~exist(NewMotFilePath)&&isfolder(NewMotFileDIR)
    copyfile(refModelPath,NewMotFilePath); 
    disp(['파일을 복사했습니다.',NewMotFilePath]);
end

end