function ResultCSVPath=exportJMAGOnlyHasAllCaseTables(app,curStudyObj,ProjName)
%%dev
    % CurrentFilePath ='Z:\01_Codes_Projects\git_fork_emach\tools\jmag\Designer\Result\ResultTable\exportJMAGAllCaseTables.m'
% 
    %%  Get Grph In PJT
    % GraphDMObj      =app.GetDataManager();
    CurrentFilePath =mfilename("fullpath");
    [MfileDir,~,~]        =fileparts(CurrentFilePath);
    for DirIndex=1:5 % Result, Designer,jmag,tools
        [MfileDir,~,~]        =fileparts(MfileDir);
    end
    MfileDir=fullfile(MfileDir,'mlxperPJT');
    if nargin>1
        MfileDir=fullfile(MfileDir,ProjName);
    end

     portNumber=getPCRDPPortNumber;
     fileDirPerPort =fullfile(MfileDir,['From',num2str(portNumber)]);
     if ~exist(fileDirPerPort,"dir")
         mkdir(fileDirPerPort)
     end
     MfileDirperPort=fullfile(fileDirPerPort);
    %% DataExport
     StudyName           =curStudyObj.GetName;
     % JMAGPJTName         =app.GetProjectName;
     [~,JMAGPJTName,~]=fileparts(app.GetProjectFolderPath);
     ResultCSVName       =[JMAGPJTName,'_',StudyName,'.csv'];        
     tempCsvPath       =fullfile(MfileDirperPort,ResultCSVName); 
     ResultCSVPath      =tempCsvPath;
      %% CSV 만들기
     ResultTableObj      =curStudyObj.GetResultTable;
     ResultTableObj.WriteAllCaseTables(tempCsvPath,'Time')
     
end
