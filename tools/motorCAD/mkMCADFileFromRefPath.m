function NewMotFilePath= mkMCADFileFromRefPath(refModelPath,AddName,additionalOption)
 
    [refModelDir,refModelMotFileName,FileExt]=fileparts(refModelPath);    
    
    if strcmp(AddName,'normal')
    NewMotFileDIR=fullfile(fileparts(refModelDir),AddName);
    NewMotFileName=[refModelMotFileName,AddName];
    elseif strcmp(AddName,'SLLAW')
    PathStr=strsplit(refModelDir,'\');
    Str2Change=PathStr(contains(PathStr,'DOE'));
        if ~isempty(Str2Change)
        SLLAWMotFileDIR=strrep(refModelDir,Str2Change{:},AddName);
        NewMotFileName =strrep(refModelMotFileName,Str2Change{:},AddName);
        else
        SLLAWMotFileDIR=strrep(refModelDir,'SLFEA',AddName);
        NewMotFileName =strrep(refModelMotFileName,'SLFEA',AddName);
        end
    NewMotFileDIR   =SLLAWMotFileDIR;
    elseif strcmp(AddName,'SLFEA')
    PathStr=strsplit(refModelDir,'\');
    Str2Change=PathStr(contains(PathStr,'DOE'));
    SLLAWMotFileDIR=strrep(refModelDir,Str2Change{:},AddName);
    SLFEAMotFileDIR=strrep(SLLAWMotFileDIR,'SLLAW',AddName);
    NewMotFileDIR  = SLFEAMotFileDIR;
    %%FileName
    refModelMotFileName=strrep(refModelMotFileName,'SLLAW','');
    refModelMotFileName=strrep(refModelMotFileName,'SLFEA','');
    NewMotFileName=[refModelMotFileName,AddName];
    end

    if nargin>2
    NewMotFilePath=fullfile(NewMotFileDIR,[NewMotFileName,additionalOption,FileExt]);
    else
    NewMotFilePath=fullfile(NewMotFileDIR,[NewMotFileName,FileExt]);
    end
    % NewMotFile 의  Lab Folder Dir
    NewMotFileLabDir=fullfile(NewMotFileDIR,[NewMotFileName,'\Lab']);
    % 폴더 생성
    if ~isfolder(NewMotFileDIR)
        mkdir(NewMotFileDIR);
    end    
    % addpath(NewMotFileDIR)
    %% 파일생성 CheckN Move 할때도 Lab 폴더 있는지 확인하고 생성
    if ~isfolder(NewMotFileLabDir)
    checkFileNMove(NewMotFilePath)    
    end
    %% 
    if ~exist(NewMotFilePath)&&isfolder(NewMotFileDIR)
        copyfile(refModelPath,NewMotFilePath); 
        disp(['파일을 복사했습니다.',NewMotFilePath]);
    end
end