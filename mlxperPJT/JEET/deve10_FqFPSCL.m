app             =callJmag
CoilPattern=4;
Modelcase  =2;
ModeltableList=cell(CoilPattern*Modelcase,2);
defaultJEETPath='Z:\Simulation\JEETACLossValid_e10_v24\JMAG';
JPJTList=findJPJTFiles(defaultJEETPath);
BoolWireTemp=JPJTList(contains(JPJTList,'Peri','IgnoreCase',true))';
BoolPeriTemp=JPJTList(contains(JPJTList,'Pattern','IgnoreCase',true))';
MQSList=[BoolWireTemp;BoolPeriTemp];
app=callJmag;

freqEList=[200:100:rpm2freqE(20000,4)]'
maxNoiter=repmat(50,len(freqEList),1);


%% Setting JPJT

for PJTIndex=1:len(MQSList)
    app=callJmag;
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
    FPConObj.SetValue("ReferredPlotFile_CurrentProject_StudyId", 18)
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
    job.SetValue("Queued", False)
    job.SetValue("DeleteScratch", True)
    job.SetValue("NumOfJobs", 1)
    job.SetValue("CheckConflict", False)
    job.SetValue("IgnoreGeometryError", False)
    job.Submit(True)
end

%%
ResultFilePath=findCSVFiles(pwd);
ResultFilePath=ResultFilePath(contains(ResultFilePath,'Pattern',"IgnoreCase",true));
ResultFilePath=ResultFilePath(contains(ResultFilePath,'Fq',"IgnoreCase",true));
ResultFilePath=ResultFilePath(~contains(ResultFilePath,'Map',"IgnoreCase",true));

resultTableCell=cell(length(ResultFilePath),1);
AppNumStudies=length(ResultFilePath);
for AppStudyIndex=1:AppNumStudies
    % opts=detectImportOptions(ResultFilePath{7})
    opts=delimitedTextImportOptions('NumVariables',1500);
    if exist(ResultFilePath{AppStudyIndex},"file")
        resultTableCell{AppStudyIndex,1}=readtable(ResultFilePath{AppStudyIndex},opts);
        resultTableCell{AppStudyIndex,2}=ResultFilePath{AppStudyIndex};
    end
end
% 
% PJTPath         =app.GetProjectFolderPath
% Model           =app.GetCurrentModel
% StudyIndex      =2
% curStudyObj     =Model.GetStudy(StudyIndex-1)
% curStudyObj.GetName

% LossStudyResultTableObj=curStudyObj.GetResultTable;
% get DataStruct
% jouleDataStruct   = getJMagResultDatas(LossStudyResultTableObj,'Joule');
% ResultCSVPath     =exportJMAGAllCaseTables(app,'JEET');
% Part Data

FqfilterName={'Fq'};
parsedMSResultTableFromCSV=readJMAGWholeResultTables(FqfilterName);
tempJouleLossTable=parsedMSResultTableFromCSV{1}.("JouleLoss:W"){caseIndex(1)}
PartNameList      =tempJouleLossTable.Properties.VariableNames';
MQSSCLoadTable=parsedMSResultTableFromCSV{1}

targetName='Total';
% TotalJoule4Case=cell(length(speedList),1);
for TableIndex=2:2
    for caseIndex=1:height(MQSSCLoadTable)
    % speed2Plot=speedList(caseIndex);    
    table2Plot=MQSSCLoadTable{caseIndex,TableIndex}{1};
    varNames=table2Plot.Properties.VariableNames;
    % calc
    TotalJoule{caseIndex}=table2Plot(:,'Total');
    end
end

%% DTTable
ParameterListTable=getJMAGDesingTable(curStudyObj);

Bool45degIndex=contains(ParameterListTable.("Equation parameters: MCADPhaseAdvance"),'45')


speedList=ParameterListTable.("Equation parameters: speed")(Bool45degIndex)
 
Total45degJoule=TotalJoule(Bool45degIndex)

FreqList=convertCharCell2Numeric(plot2Table.Properties.RowNames)
RPMList=freq2rpm(elec2mech(FreqList,4))
for tableIndex=1:len(Total45degJoule)
plot2Table=Total45degJoule{tableIndex}
plot(RPMList,plot2Table.('Total')/1000,'DisplayName',speedList{tableIndex})
hold on
end