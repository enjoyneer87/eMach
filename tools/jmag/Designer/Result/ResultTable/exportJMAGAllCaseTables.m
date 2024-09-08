function ResultCSVPath=exportJMAGAllCaseTables(app,ProjName)
%%dev
    % CurrentFilePath ='Z:\01_Codes_Projects\git_fork_emach\tools\jmag\Designer\Result\ResultTable\exportJMAGAllCaseTables.m'
% 
    %%  Get Grph In PJT
    GraphDMObj      =app.GetDataManager();
    appNumStudies=app.NumStudies;
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
    
    for PJTStudyIndex=1:appNumStudies
        curStudyObj=app.GetStudy(PJTStudyIndex-1);
        if curStudyObj.HasResult
           DTObj               =curStudyObj.GetDesignTable;
           NumCases            =DTObj.NumCases;
           ResultFileNamesCell =curStudyObj.GetResultFileNames;
           StudyName           =curStudyObj.GetName;
           JMAGPJTName         =app.GetProjectName;
           ResultCSVName       =[JMAGPJTName,'_',StudyName,'.csv'];        
           tempCsvPath       =fullfile(MfileDirperPort,ResultCSVName); 
           ResultCSVPath{PJTStudyIndex}      =tempCsvPath;
            %% CSV 만들기
           ResultTableObj      =curStudyObj.GetResultTable;
           ResultTableObj.WriteAllCaseTables(tempCsvPath,'Time')
        end
    end
end

        % ResultFile4Path     =curStudyObj.GetResultFileName;
        % PathInfoList        =strsplit(ResultFile4Path,'/');
        % jplotName           =PathInfoList(end);
        % caseName            =PathInfoList(end-1);
        % StudyName           =PathInfoList(end-2);
        % ModelName           =strrep(PathInfoList(end-3),'~','');