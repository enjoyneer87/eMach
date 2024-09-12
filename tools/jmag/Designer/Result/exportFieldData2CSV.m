function  exportFilePathList=exportFieldData2CSV(app,ResultType,JMAGPJTName,PartIdList,ModelString,StudyString)
% ResultType='B';
% ResultType='J';
% ResultType='M';
% ResultType='A';

% %% dev
% ModelString='ref'
% JMAGPJTName='JEET'
% StudyString='_Load_18k_rgh'
% CurrentFilePath='D:\KangDH\Emlab_emach\tools\jmag\Designer\Result\exportFieldData2CSV.m'
% CurrentFilePath='Z:\01_Codes_Projects\git_fork_emach\tools\jmag\Designer\Result\file.m'
% % ***** Default Setting
%% Define Save Path
    CurrentFilePath =mfilename("fullpath");
    [MfileDir,~,~]        =fileparts(CurrentFilePath);
    for DirIndex=1:4 % Result, Designer,jmag,tools
        [MfileDir,~,~]        =fileparts(MfileDir);
    end
    MfileDir=fullfile(MfileDir,'mlxperPJT');
    if nargin>2
        MfileDir=fullfile(MfileDir,JMAGPJTName);
    end
    
     portNumber=getPCRDPPortNumber;
     fileDirPerPort =fullfile(MfileDir,['From',num2str(portNumber)]);
     if ~exist(fileDirPerPort,"dir")
         mkdir(fileDirPerPort)
     end
     MfileDirperPort=fullfile(fileDirPerPort);
% get All Model Name & Study Name
    [JprojStruct,NumModels,ModelStudy] = getJProjHierModelStudyTable(app);
    ModelNames=fieldnames(JprojStruct);
    
    % filter Model
    if nargin>2&~isempty(ModelString)
    BoolModel=contains(ModelNames,ModelString,"IgnoreCase",true);
    FilteredModelTable=JprojStruct.(ModelNames{BoolModel});
    else
    FilteredModelTable=JprojStruct;
    end
% filter Studies
    if nargin>3&~isempty(StudyString)
    BoolStudy=contains(FilteredModelTable.StudyName,StudyString,"IgnoreCase",true);
    StudyObjCell=FilteredModelTable.StudyObj(BoolStudy);
    CSVIndex=1;
    exportFilePathList=cell(1,1);
    %% **** KeyPoint Designer
    for PJTStudyIndex=1:length(StudyObjCell)
        curStudyObj=StudyObjCell{PJTStudyIndex};
        if curStudyObj.HasResult
           NumCases =curStudyObj.GetDesignTable().NumCases();
           for CasesIndex=1:1
           curStudyObj.SetCurrentCase(CasesIndex-1)
           StudyName=curStudyObj.GetName;
           ResultCSVName       =[JMAGPJTName,'_',StudyName,'_case',num2str(CasesIndex),'.csv'];        
           tempCsvPath       =fullfile(MfileDirperPort,ResultCSVName); 
           %%export CSV            
           exportFilePath=strrep(tempCsvPath,'.csv',['_',ResultType,'.csv']);
           selJMagDesignerObj(app,PartIdList);       
           exportFilePathList{CSVIndex,1}=exportJMAGFieldTable(curStudyObj,'All',ResultType,exportFilePath);
           CSVIndex=CSVIndex+1;
           end
        end
    end    
    else
    %% **** KeyPoint Designer
    for PJTStudyIndex=1:appNumStudies
        curStudyObj=app.GetStudy(PJTStudyIndex-1);
        if curStudyObj.HasResult
           NumCases =curStudyObj.GetDesignTable().NumCases();
           for CasesIndex=1:NumCases
           curStudyObj.SetCurrentCase(CasesIndex-1)
           ResultCSVName       =[JMAGPJTName,'_',StudyName,'_case',num2str(CasesIndex),'.csv'];        
           tempCsvPath       =fullfile(MfileDirperPort,ResultCSVName); 
           %%export CSV            
           exportFilePath=strrep(tempCsvPath,'.csv',['_',ResultType,'.csv']);
           selJMagDesignerObj(app,PartIdList);       
           exportFilePath=exportJMAGFieldTable(curStudyObj,'All',ResultType,exportFilePath,PartIdList);   
           end
        end
    end
    end



    %% 
%         end
%     exportData=struct();
% % Jproject File Path
%     JMAG=app;
%     file_path=JMAG.GetProjectPath();
% % Project Name
%     [~, fileName,~]=fileparts(file_path);
%     % app.SetProjectName(fileName);
%     % pjt_name=app.GetProjectName() ;  
% %   파일이 켜져있지 않으면 파일명 읽어서 열기
% %% Find Model& study Name
%     ModelName=JMAG.GetCurrentModel.GetName();
%     StudyName=JMAG.GetCurrentStudy.GetName();
%     Simulation.ModelName=ModelName;
%     Simulation.StudyName=StudyName;
% % Check for New Results
%     JMAG.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName).CheckForNewResults();
% % for number_case
%     JStudy   =JMAG.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName);
%     NumCases =JStudy.GetDesignTable().NumCases();
% 
% 
% %% Model 단위 [Tobe]
% %%study 단위에서
% check_case = struct('result_exist', false, 'caseno', 0); % Preallocation을 위한 초기 배열 생성
% check_case = repmat(check_case, NumCases, 1); % 배열 크기를 미리 할당
% 
% %% Result Check
% for i=1:NumCases
%     Hasresult=JStudy.CaseHasResult(i-1);
%     check_case(i).result_exist=Hasresult;
%     check_case(i).caseno=i;
% end
% 
% %% 
% for i=1:NumCases
%     if check_case(i).result_exist==1
%         % Select Air region
%         JMAG.View().SetCurrentCase(i)
%         selectAirByWorldPosSOD(i_Stator_OD,JMAG);
%         % Slice Condition Number
%         % Num_condition=Num_condition_slice(Simulation);
%         Num_condition=0;
%         selectObj='All';
%         % export with skew check
%         exportFilePath=exportJMAGResultTable(JMAG,Simulation,i,selectObj,Num_condition,0);
%         exportData(i).case=i;
%         exportData(i).exportFilePath=exportFilePath;
%     end
% end


end

