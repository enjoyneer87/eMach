app             =callJmag
%% Set DefaultPath
%% Set DefaultPath
CoilPattern=4;
Modelcase  =2;
ModeltableList=cell(CoilPattern*Modelcase,2);
PortNumber=getPCRDPPortNumber();
if PortNumber==38100
    defaultPath='D:\KangDH\Thesis\e10\JMAG';
    defaultJEETPath='D:\KangDH\Emlab_emach\mlxperPJT\JEET\From38100\';
elseif PortNumber==38002
    defaultPath='Z:/Simulation/JEETACLossValid_e10_v24/JMAG';
    defaultJEETPath='Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\From38002\';
end
%% Find PJT
JPJTList=findJPJTFiles(defaultPath);
BoolWireTemp=JPJTList(contains(JPJTList,'Peri','IgnoreCase',true))';
BoolPeriTemp=JPJTList(contains(JPJTList,'Pattern','IgnoreCase',true))';
BoolREFTemp=JPJTList(contains(JPJTList,'SCL','IgnoreCase',true))';

MQSList=[BoolREFTemp];
app=callJmag;

freqEList=[200:100:rpm2freqE(20000,4)]'
maxNoiter=repmat(50,len(freqEList),1);


%% Setting JPJT

for PJTIndex=1:len(MQSList)
    % app=callJmag;
    app.Load(MQSList{PJTIndex})
    app.Show
    ModelObj=app.GetCurrentModel;
    ModelObj.RestoreCadLink
    geomApp=app.CreateGeometryEditor();
    curStudyObj=app.GetCurrentStudy;
    curStName=curStudyObj.GetName();
    if ~contains(curStName,'Fq','IgnoreCase',true)
  
    [~,PJTFileName,~]=fileparts(MQSList{PJTIndex});
    %% mk FP Condition
    PJTJfilesPath=app.GetProjectFolderPath;
    subPath      =dir(PJTJfilesPath);
    % DT Case Control
    DTTableObj=curStudyObj.GetDesignTable();
    % DTTableObj.AddParameterVariableName("FP (FrozenPermeability): ReferredPlotFile_CurrentProject_CaseId")
    ParameterListTable=getJMAGDesingTable(curStudyObj);
    varName  =ParameterListTable.Properties.VariableNames;
    paraName  =varName(contains(ParameterListTable.Properties.VariableNames,'speed'));
    ParameterListTable(:,paraName{1}).Variables=cellstr(num2str([1000:3000:3000*(height(ParameterListTable)-1)+1000]'));
    paraName  =varName(contains(ParameterListTable.Properties.VariableNames,'Phase'));
    ParameterListTable(:,paraName{1}).Variables=repmat({'43.3'},height(ParameterListTable),1);
    settedDTTable=setJMAGDesingTable(curStudyObj,ParameterListTable);
    curStudyObj.GetStudyProperties().SetValue("MultiCPU", 8)
    app.Save()
    end
    %% Submit Job
    job = curStudyObj.CreateJob();
    job.SetValue("Title", PJTFileName)
    job.SetValue("Queued", false)
    job.SetValue("DeleteScratch", true)
    job.SetValue("NumOfJobs", 1)
    job.SetValue("CheckConflict", false)
    job.SetValue("IgnoreGeometryError", false)
    job.Submit(true)
end
%% Export Result
for PJTIndex=1:len(MQSList)
    % app=callJmag;
    app.Load(MQSList{PJTIndex})
    app.CheckForNewResults()
    exportJMAGAllCaseTables(app,'JEET')
end
%% Get Result
FqfilterName={'e10_WTPM_Pattern'};
MatFileName='MQS TS FEA';
[parsedMSResultTableFromCSV,ResultCSVPath]=readJMAGWholeResultTables(FqfilterName);
AppNumStudies=len(parsedMSResultTableFromCSV);
% save([defaultJEETPath,MatFileName,'.mat'],"parsedMSResultTableFromCSV")

MatFileList=findMatFiles(pwd);
MatFileList=MatFileList(contains(MatFileList,FqfilterName,"IgnoreCase",true));
MatFileList=MatFileList(~contains(MatFileList,'Fq',"IgnoreCase",true));
AppNumStudies=len(MatFileList);
PatternList={'PatternC','PatternD'};


for AppStudyIndex=1:AppNumStudies
    load(MatFileList{AppStudyIndex})
    if contains(MatFileList{AppStudyIndex},'SCL')
    figure(2)
    DispName='SLC'
    else
    figure(1)
    DispName='REF';
    end
    %%
    tempJouleLossTableCell=parsedResultTable5StudyPerStudy.("JouleLoss:W");
    JouleAvgTablCell4Case=cell(len(speedList),2);
    speedList=zeros(1,len(tempJouleLossTableCell));
    speedNameList=cell(1,len(tempJouleLossTableCell));
    for caseIndex=1:height(tempJouleLossTableCell)
        table2Plot=tempJouleLossTableCell{caseIndex};
        tempJouleLossTable{caseIndex}        =table2Plot.Total;
        speedList(caseIndex)=freqE2rpm(1/seconds(table2Plot.Time(121)),4);
        speedNameList{1,caseIndex}=['case',num2str(caseIndex),'speed',num2str(speedList(caseIndex))];
        JouleAvgTablCell4Case{caseIndex,2}=mean(table2Plot(end-120:end,'Total').Variables);
        JouleAvgTablCell4Case{caseIndex,1}=table2Plot(end-120:end,'Total').Variables;
    end
    JouleAvgTablCell4CaseTable=cell2table(JouleAvgTablCell4Case);
    JouleAvgTablCell4CaseTable.Properties.VariableNames={'JouleTable','JouleAvg'};
    meanACLoss=[JouleAvgTablCell4Case{:,2}];
    if contains(MatFileList{AppStudyIndex},'PatternC')
        PatternIndex=1;
    else
        PatternIndex=2;
    end
    plot(speedList,meanACLoss,'DisplayName',PatternList{PatternIndex});
    title(DispName)
    hold on
    % JouleAvgTablCell4CaseTable.Properties.RowNames=speedList;
    % save([defaultJEETPath,MatFileName,num2str(AppStudyIndex),'.mat'],"JouleAvgTablCell4CaseTable")
end




%% DTTable
ParameterListTable=getJMAGDesingTable(curStudyObj);
RPMList  =freq2rpm(elec2mech(freqEList,4));


