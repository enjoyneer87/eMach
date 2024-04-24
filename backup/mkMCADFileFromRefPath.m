function NewMotFilePath= mkMCADFileFromRefPath(refModelPath,AddName)
    [refModelDir,refModelMotFileName,FileExt]=fileparts(refModelPath);    
    
    if strcmp(AddName,'normal')
    NewMotFileDIR=fullfile(fileparts(refModelDir),AddName);
    elseif strcmp(AddName,'SLLAW')
    SLLAWMotFileDIR=strrep(refModelDir,'DOE',AddName);
    NewMotFileDIR   =SLLAWMotFileDIR;
    elseif strcmp(AddName,'SLFEA')
    SLLAWMotFileDIR=strrep(refModelDir,'DOE',AddName);
    SLFEAMotFileDIR=strrep(SLLAWMotFileDIR,'SLLAW',AddName);
    NewMotFileDIR  = SLFEAMotFileDIR;
    end

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