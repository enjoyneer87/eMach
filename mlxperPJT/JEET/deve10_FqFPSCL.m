
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
BoolREFTemp=JPJTList(contains(JPJTList,'REF','IgnoreCase',true))';

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
    FQcurStName=[curStName,'_Fq'];
    FqStudyObj=ModelObj.DuplicateStudyWithType(curStName, "Frequency2D", FQcurStName, true);
    end
    %% mk FP Condition
    FPConObj=FqStudyObj.CreateCondition("FrozenPermeability", "FP");
    refarray=num2cell([freqEList,maxNoiter]);
    app.GetDataManager().CreatePointArray("point_array/frequency_vs_nonlinear", "SCLFreqList")
    app.GetDataManager().GetDataSet("SCLFreqList").SetName("SCLFreqList")
    app.GetDataManager().GetDataSet("SCLFreqList").SetTable(refarray)
    FqStudyObj.GetStep().SetValue("Step", 12)
    FqStudyObj.GetStep().SetValue("StepType", 2)
    FqStudyObj.GetStep().SetTableProperty("Nonlinear", app.GetDataManager().GetDataSet("SCLFreqList"))
    % FP Con Setting
    FPConObj.SetValue("ReferredPlotFile_DataSourceType", 2)
    % Get Study ID
    PJTJfilesPath=app.GetProjectFolderPath;
    subPath      =dir(PJTJfilesPath);
    % isDirSub=[subPath.isdir];
    subPathNameList={subPath.name};
    ModelFolderName=contains(subPathNameList,ModelObj.GetName,"IgnoreCase",true);
    ModelPath      =fullfile(PJTJfilesPath,subPath(ModelFolderName).name);
    folderNameList=findFolderNames(ModelPath);
    folderNameList=folderNameList(~contains(folderNameList,'Fq','IgnoreCase',true));
    StuydFolderNames=folderNameList(contains(folderNameList,'~'));
    if len(StuydFolderNames)==1
        splitedList=strsplit(StuydFolderNames{1},'~');
        StudyId=splitedList(end);
    end
    FPConObj.SetValue("ReferredPlotFile_CurrentProject_StudyId", int32(convertCharCell2Numeric(StudyId)))
    FPConObj.SetCoordinateSystem("ReferredPlotFile_CoordinateId", "Global Rectangular")
    FPConObj.ClearParts()
    PartStruct      =getJMAGDesignerPartStruct(app);
    PartStructByType=convertJmagPartStructByType(PartStruct);
    sel = FPConObj.GetSelection();
    sel.SelectPart(PartStructByType.StatorCoreTable.partIndex)
    sel.SelectPart(PartStructByType.RotorCoreTable.partIndex)
    FPConObj.AddSelected(sel)
    FPConObj.SetValue("StartStep", 361)
    FPConObj.SetValue("EndStep", 481)
    FPConObj.SetValue("UseAverage", 1)
    % DT Case Control
    DTTableObj=FqStudyObj.GetDesignTable();
    DTTableObj.AddParameterVariableName("FP (FrozenPermeability): ReferredPlotFile_CurrentProject_CaseId")
    ParameterListTable=getJMAGDesingTable(FqStudyObj);
    varName  =ParameterListTable.Properties.VariableNames;
    paraName  =varName(contains(ParameterListTable.Properties.VariableNames,'FrozenPermeability'));
    ParameterListTable(:,paraName{1}).Variables=[1:1:height(ParameterListTable)]';
    paraName  =varName(contains(ParameterListTable.Properties.VariableNames,'Phase'));
    ParameterListTable(:,paraName{1}).Variables=repmat({'43.3'},height(ParameterListTable),1);
    settedDTTable=setJMAGDesingTable(FqStudyObj,ParameterListTable);
    app.Save()
    %% Submit Job
    job = FqStudyObj.CreateJob();
    job.SetValue("Title", "SC_e10_WirePeriodic_Load_FQ")
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
FqfilterName={'Fq'};
MatFileName='MQS FQ FEA';
[parsedMSResultTableFromCSV,ResultCSVPath]=readJMAGWholeResultTables(FqfilterName);
AppNumStudies=len(parsedMSResultTableFromCSV);
% save([defaultJEETPath,MatFileName,'.mat'],"parsedMSResultTableFromCSV")

MatFileListFq=findMatFiles(pwd);
MatFileListFq=MatFileListFq(contains(MatFileListFq,FqfilterName,"IgnoreCase",true));
PatternList={'PatternC','PatternD'};
figure(1)
for AppStudyIndex=1:AppNumStudies
    load(MatFileListFq{AppStudyIndex})
    parsedResultTable5StudyPerStudy
    tempJouleLossTableCell=parsedResultTable5StudyPerStudy.("JouleLoss:W");
    for caseIndex=1:height(tempJouleLossTableCell)
        tempJouleLossTable{caseIndex}        =tempJouleLossTableCell{caseIndex}.Total;
    end
    for tableIndex=1:1
        plot2Table=Total45degJoule{tableIndex};
        plot(RPMList,plot2Table/1000,'DisplayName',['FQ-MQS FEA ',PatternList{AppStudyIndex}])
        legend
        hold on
    end
end
%% DTTable
ParameterListTable=getJMAGDesingTable(curStudyObj);
RPMList  =freq2rpm(elec2mech(freqEList,4));


