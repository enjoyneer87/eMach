%% dev 
% % Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\deve10MQSplotAC.m에서 활용
% Circuit 생성 어떻게 할지 결정
% - Winding은 jmdl 불러오는거니까 - circuit도?
% ApplyJMAGAnalysisTemplate에 Template있는데 circuit이랑, study네임 미지정
% 기본 study는 NoLoad로 하고, Circuit Input도 없는걸로하고
% Mesh 설정끝나면
% Study 복사후 복사한 스터디들 Circuit Input 넣기
%% from
%  devJmagSettingwithConductor
% Z:\01_Codes_Projects\git_fork_emach\tools\jmag\devJmagWindingSetting.mlx
%% MCAD
% in origin MLX 
%%% ***** 먼저 실행 JEETResult_rev1.mlx

% 이 파일은 JMAG Jproj 호출을 위한 m파일입니다
%% rev1에서 회전자 dxf 수정함
refPath='Z:\Simulation\JEETACLossValid_e10_v24\refModel\e10_UserRemesh.mot';
if ~exist(refPath,"file")
    refPath='D:\KangDH\Thesis\e10\refModel\e10_UserRemesh.mot';
end
[refDIR,FileName,~]=fileparts(refPath);
dxfFiles = findDXFFiles(refDIR)';
%% JMAG
app=callJmag('231');
app.Show
jprojFiles=app.GetProjectFolderPath;
jprojPath='Z:\Simulation\JEETACLossValid_e10_v24\JMAG\e10_JFT145_WireTemp.jproj';
[~,jprojName,~]=fileparts(jprojPath);
if ~exist(jprojPath,"file")
    jprojPath=fullfile(refDIR,[jprojName,'.jproj']);
end
if contains(jprojFiles,'C:/Users/','IgnoreCase',true)
    if ~exist(jprojPath,"file")
    app.SaveAs(jprojPath)
    end
end
app.Load(jprojPath)
ModelObj=app.GetCurrentModel;
jprojFiles=app.GetProjectFolderPath;

% Model.SetStudyOrder("NoLoad", 0)
%% 
StepDivision=120;
EndTime=1/FreqE;
%% Import
% dxfList2Import=defDXFList2Import(dxfFiles, 5,3);
% delete(DXFMatFilePath)

DXFMatFilePath=fullfile(jprojFiles,'ImportDXF.mat');
if ~exist(DXFMatFilePath,"file")
    save(DXFMatFilePath,'dxfList2Import');
else
    load(DXFMatFilePath);
end
ModelObj=app.GetCurrentModel;
if ModelObj.IsValid
    ModelObj.RestoreCadLink()
end
geomApp=app.CreateGeometryEditor(0);

% Check Exist Assem N Import
AssemTable = getGeomAssemItemListTable(geomApp);

% delete2AssemInJMAG= 'Rotor';
delete2AssemInJMAG=[];
if exist('AssemTable',"var")&~isempty(delete2AssemInJMAG)
    delete2AssemTable=AssemTable(contains(AssemTable.AssemItemName,delete2AssemInJMAG),:);
    if isempty(AssemTable)
    sketchs=ImportDXF2Geom(dxfList2Import,geomApp);
    else 
    geomApp.GetDocument().GetSelection().Add(delete2AssemTable.AssemItem);
    geomApp.GetDocument().GetSelection().Delete()
    dxfList2Import=dxfList2Import(contains(dxfList2Import.sketchName,delete2AssemInJMAG),:);
    sketchs       =ImportDXF2Geom(dxfList2Import,geomApp);
    end
elseif ~exist('AssemTable',"var")
    sketchs=ImportDXF2Geom(dxfList2Import,geomApp);
elseif isempty(AssemTable)
    sketchs=ImportDXF2Geom(dxfList2Import,geomApp);
end

%% setGet GeomAssemTable 
StatorAssemRegionTable=setGetGeomStatorNameNTable(geomApp);
RotorAssemRegionTable =setGetGeomRotorNameNTableInnerRotor(geomApp);

%% GeomDesginTable
% [Skip] GeomDesginTable
setGeomDesignTable('stack_length',MachineData.Stator_Lam_Length,app);
% setGeomDesignTable('Freq',Freq,app);
setGeomDesignTable('SLOTS',MachineData.Slot_Number,app);
setGeomDesignTable('POLES',MachineData.Pole_Number,app);

% Get Mirror or Feature 

% Mirror
mirrorRotorRegion(RotorAssemRegionTable,geomApp)

% Suppress Shaft
geomAssem=geomApp.GetDocument().GetAssembly();

% geomAssem.GetItem("Rotor").OpenSketch()
% geomAssem.GetItem("Rotor").GetItem("Shaft").SetProperty("Suppress", 1)
% geomAssem.GetItem("Rotor").CloseSketch()
%
RotorRegionTablePerType = detRotorRegionTablePerType(RotorAssemRegionTable);
StatorRegionTablePerType = detStatorRegionTablePerType(StatorAssemRegionTable);

%% lineTable
StatorGeomLineTable=getLineTable(StatorAssemRegionTable);

%%% Arc 
StatorGeomArcTable     =getArcTable(StatorAssemRegionTable);
RotorGeomArcTable      =getArcTable(RotorAssemRegionTable);
runnerType             =checkInnerOuterMotor(StatorGeomArcTable,RotorGeomArcTable);
StatorOneSlotAngle     =max(max(StatorGeomArcTable.EndVertexTabletheta),max(StatorGeomArcTable.StartVertexTabletheta));

%% if no WireTemplate and ConductorTable is not Empty
% Import Stator Taemplate and Delete exist Stator Assem
jmdlFileName='JFT145_stator';
filePathCell=findFilePaths(jmdlFileName,fileparts(jprojFiles));
if isempty(filePathCell)
    filePathCell=findFilePaths(jmdlFileName,pwd);
end
jmdlfilePath=filePathCell{:};
if ~any(contains(StatorAssemRegionTable.Type,'WireTemplate'))&~isempty(StatorRegionTablePerType.ConductorTable)
    %% Dimension
    MaxEndVertexTabler          =max(StatorGeomArcTable.EndVertexTabler);
    MaxStartVertexTabler        =max(StatorGeomArcTable.StartVertexTabler);
    SOD                         =2*max(MaxEndVertexTabler,MaxStartVertexTabler);
    MinEndVertexTabler          =min(StatorGeomArcTable.EndVertexTabler);
    MinStartVertexTabler        =min(StatorGeomArcTable.StartVertexTabler);
    SID                         =2*min(MinEndVertexTabler,MinStartVertexTabler);
    %% [TC]
    BackyokeLength              =10;
    StatorGeoAssemName='Stator';
    existSTItemObj=geomAssem.GetItem(StatorGeoAssemName);
    if ~existSTItemObj.IsValid
    StatorGeoAssemName='stator';
    existSTItemObj=geomAssem.GetItem(StatorGeoAssemName);
    end
    geomApp.GetDocument().GetSelection().Add(existSTItemObj) 
    geomApp.GetDocument().GetSelection().Delete()
      %% merge 
    geomApp.MergeJmdl(jmdlfilePath)
    preAssembleName="StatorWithTemplate";
    StatorObj=geomAssem.GetItem(preAssembleName);
    if ~StatorObj.IsValid
        NumItems=geomAssem.NumItems;
        for ItemIndex=1:NumItems
        StatorObjList{ItemIndex}=geomAssem.GetItem(int32(ItemIndex)-1); 
            if StatorObjList{ItemIndex}.IsValid
                StatorObjName{ItemIndex}=StatorObjList{ItemIndex}.GetName;
                if contains(StatorObjName{ItemIndex},'stator','IgnoreCase',true)
                    StatorObj=StatorObjList{ItemIndex};
                end
            end
        end
    end
    StatorObj.SetName(StatorGeoAssemName);
    %% Wire Template Coincident
    ref1 = geomAssem.GetItem(StatorGeoAssemName).GetItem("Line.6");
    ref2 = geomApp.GetDocument().CreateReferenceFromItem(ref1);
    ref3 = geomAssem.GetItem(StatorGeoAssemName).GetItem("Line");
    ref4 = geomApp.GetDocument().CreateReferenceFromItem(ref3);
    geomAssem.GetItem(StatorGeoAssemName).CreateBiConstraint("coincident", ref2, ref4)
    geomAssem.GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("RectangleWidth", 1.6)
    geomAssem.GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("RectangleHeight", 3.7)
    geomAssem.GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("WireCoatingThickness", 0.1)
    geomAssem.GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("WieGapDistance", 0.15)
    geomAssem.GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("WireCount", 4)
    geomAssem.GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("FillFactor", 63.8825526278559)
    geomAssem.GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("StartDeltaX", 5)
    geomAssem.GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("StartDeltaY", "5*tan(3.75*pi/180)")
    
    %% set Geom Contraint
    SW4Obj=StatorObj.GetItem('SW4');
    SW4Obj.IsValid
    SW4Obj.SetDistance(BackyokeLength)
    geomAssem.GetItem(StatorGeoAssemName).GetItem("SD1").SetProperty("Diameter", SOD);
    geomAssem.GetItem(StatorGeoAssemName).GetItem("SD4").SetProperty("Diameter", SID);
end
%% 자석 edge잡기 & Stator Pattern
if exist('delete2AssemInJMAG','var') &~isempty(delete2AssemInJMAG)
    if contains(delete2AssemInJMAG, 'Rotor')
    getGeomMagnetizationEdgeSet(RotorAssemRegionTable,geomApp);
    elseif contains(delete2AssemInJMAG, 'Stator')
    % Stator pattern
    createCircPattern4withInput(StatorAssemRegionTable,'',geomApp)
    end
elseif ~exist('AssemTable',"var")
% else % initial
    getGeomMagnetizationEdgeSet(RotorAssemRegionTable,geomApp);
    if ~contains(StatorAssemRegionTable.Type,'WireTemplate')
    createCircPattern4withInput(StatorAssemRegionTable,'',geomApp);
    end
elseif isempty(AssemTable)
    getGeomMagnetizationEdgeSet(RotorAssemRegionTable,geomApp);
end
%% Import 
app.ImportDataFromGeometryEditor();
%% Designer ModelObj
ModelObj=app.GetCurrentModel;
WireTemplateObj=getWireTemplateObject(geomApp);

if WireTemplateObj.IsValid
    isConductor=2; % wireTemplate
elseif isempty(StatorRegionTablePerType.ConductorTable)
    isConductor=1;
else
    isConductor=0;
end

if isConductor==1
    ModelName='e10_Conductor';
    ConductorModelObj=ModelObj;
    ConductorMeshSize=0.5;
elseif isConductor==2
    ModelName='e10_WireTemplate';
    ConductorModelObj=ModelObj;
    ConductorMeshSize=0.5;
else
    ModelName='e10_Coil';
    CoilModelObj=ModelObj;
    ConductorMeshSize=1;
end

ModelObj.SetName(ModelName)
ModelName=ModelObj.GetName;
app.SetCurrentModel(ModelName)


%% ungroup
rmJModelAllGroups(app)
% oldFileName='writeJmagWindingPatternCSV'
% newFileName='devWriteJmagWindingPatternCSV'
% renameFile(newFileName,oldFileName)

%% Model PartName Change & Model Set - PartStruct
PartStruct          =getJMAGDesignerPartStruct(app);
PartTable           =struct2table(PartStruct);

PartStructByType    =convertJmagPartStructByType(PartStruct);

% stator CoreName
changeJMAGPartNameTable(PartStructByType.StatorCoreTable,app)
%% reGet
PartStruct          = getJMAGDesignerPartStruct(app);
PartStructByType    = convertJmagPartStructByType(PartStruct);
fieldList = fields(PartStructByType);

%% 
% %% 기본 assem이름 일원화
% NamseSplit=strsplit(PartTable.Name{1},'/')
% NamseSplit
% findName='Stator';
% PartTable(contains(PartTable.Name,findName,"IgnoreCase",true),:)    
% numericArray = cellfun(@(x) updatePartName(x,'Stator',1), );
% 미리 대체할 문자열을 설정
searchStrings = {'rotor', 'stator'};
replaceStrings = {'Rotor', 'Stator'};

for fieldIndex = 1:length(fieldList)
    currentField = PartStructByType.(fieldList{fieldIndex});
    
    if istable(currentField)&~isempty(currentField)
        % 각 검색 문자열에 대해 대체 작업 수행
        for i = 1:length(searchStrings)
            currentField.Name = strrep(currentField.Name, searchStrings{i}, replaceStrings{i});
        end
        
        % 수정된 테이블을 다시 구조체 필드에 할당
        PartStructByType.(fieldList{fieldIndex}) = currentField;       
    end
    changeJMAGPartNameTable(currentField,app)
end
%% Magnet
sortedMagnetTables = sortMagnetTableByNumber(PartStructByType);
%% Conductor Table
if isConductor>0 & isempty(PartStructByType.ConductorTable)
PartStructByType.ConductorTable=PartStructByType.SlotTable;
PartStructByType.SlotTable=0;
end
%%[TC] add LayerNumber sortingConductorTableBySlot
PartStructByType.ConductorPartTable=sortingConductorTableBySlot(PartStructByType.ConductorTable,app);
changeJMAGPartNameTable(PartStructByType.ConductorPartTable,app)

%% reGet
PartStruct=getJMAGDesignerPartStruct(app);
PartStructByType = convertJmagPartStructByType(PartStruct);
if isConductor>0 & isempty(PartStructByType.ConductorTable)
PartStructByType.ConductorTable=PartStructByType.SlotTable;
PartStructByType.SlotTable=0;
end
%% Change Name
ModelObj=app.GetCurrentModel;
ModelObj.SortPartsByName()
%% Make Set
SlotConductorSetName="SlotConductor";

strcell=strsplit(PartStructByType.ConductorTable.Name{1},'/');
SetObj=ModelObj.GetSetList.GetSet(SlotConductorSetName);
if ~(SetObj.IsValid)
ModelObj.GetSetList().CreatePartSet(SlotConductorSetName)
ModelObj.GetSetList().GetSet(SlotConductorSetName).SetUpdateByRelation(false)
ModelObj.GetSetList().GetSet(SlotConductorSetName).SetMatcherType("MatchNames")
ModelObj.GetSetList().GetSet(SlotConductorSetName).SetParameter("style", "prefix")
ModelObj.GetSetList().GetSet(SlotConductorSetName).SetParameter("text", [strcell{1},'/Slot'])
ModelObj.GetSetList().GetSet(SlotConductorSetName).Rebuild()
end
RotorSetName="Rotor";
SetObj=ModelObj.GetSetList.GetSet(RotorSetName);
if ~(SetObj.IsValid)
ModelObj.GetSetList().CreatePartSet(RotorSetName)
ModelObj.GetSetList().GetSet(RotorSetName).SetMatcherType("MatchNames")
ModelObj.GetSetList().GetSet(RotorSetName).SetParameter("style", "prefix")
ModelObj.GetSetList().GetSet(RotorSetName).SetParameter("text", "Rotor")
ModelObj.GetSetList().GetSet(RotorSetName).Rebuild()
end
%% createStudy or apply Template
useTemplate=1;
TemplateName='IPMSM_WireSinCond';

NumModels=app.NumModels;

for ModelIndex=1:NumModels
    ModelObj=app.GetModel(ModelIndex-1);
    NumStudies=ModelObj.NumStudies;
    if NumStudies==0
        if useTemplate==0
            for StudyIndex=1:1
            StudyNameList={'NoLoad'};
            StudyObj=ModelObj.CreateStudy('Transient2D',[ModelName,StudyNameList{StudyIndex}]);
            end
        elseif useTemplate==1
            ApplyJMAGAnalysisTemplate(TemplateName,app)
        end
    else
        disp('manual')
        NoloadStudyObj=ModelObj.GetStudy(0);
        NoloadStudyObj.GetName;
        NoloadStudyObj.SetName([ModelName,'_NoLoad'])
        loadStudyObj=ModelObj.GetStudy(1);
        loadStudyObj.GetName
        loadStudyObj.SetName([ModelName,'_Load'])
    end
end

app.Save

NumModels=app.NumModels;
for ModelIndex=1:NumModels
    ModelObj=app.GetModel(ModelIndex-1);
    NumStudies=ModelObj.NumStudies;
    %% Material Set
    BandMaterial                ='Air'                  ;
    ShaftMaterial               ='Air'                  ;
    RotorCoreMaterial           ="NO18-1160"     ;    
    MagNetMaterial              ="N42EH"         ;
    MagnetTable=PartStructByType.MagnetTable;
    NumStudies=ModelObj.NumStudies;
    for StudyIndex=1:NumStudies
        curStudyObj=ModelObj.GetStudy(StudyIndex-1);
        app.SetCurrentStudy(curStudyObj.GetName)
        % Magnet
        setMagnetMagnetizationbyEdgeSet(app,MagNetMaterial,MagnetTable)
        % Other
        curStudyObj.SetMaterialByName("Stator/StatorCore",RotorCoreMaterial)
        curStudyObj.SetMaterialByName("Rotor/RotorCore", RotorCoreMaterial)
        curStudyObj.SetMaterialByName("Band",BandMaterial)
        curStudyObj.SetMaterialByName("Shaft",ShaftMaterial)
        if isConductor>0
            for PartIndex = 1:height(PartStructByType.ConductorTable)
                curStudyObj.SetMaterialByName(PartStructByType.ConductorTable.Name{PartIndex}, "Copper");
                curStudyObj.GetMaterial(PartStructByType.ConductorTable.Name{PartIndex}).SetValue("EddyCurrentCalculation", 1);
            end
        end
    end
end
%% mkDesignerEquation
for StudyIndex=1:NumStudies
    curStudyObj=ModelObj.GetStudy(StudyIndex-1);
    app.SetCurrentStudy(curStudyObj)
    mkDesignerEquation('speed',num2str(rpm),curStudyObj)
    mkDesignerEquation('omega','speed/60*2*pi',curStudyObj,'equation')
    mkDesignerEquation('omegaE','omega*POLES/2',curStudyObj,'equation')
    mkDesignerEquation('Freq','omega/(2*pi)',curStudyObj,'equation')
    mkDesignerEquation('FreqE','omegaE/(2*pi)',curStudyObj,'equation')
    mkDesignerEquation('MCADPhaseAdvance',num2str(MCADPhaseAdvance),curStudyObj)
end

% %% Winding Setting
% CoilWindingInfo           =defCoilWindingInfoStruct(MachineData);
% firstSlotWirePartsTable   =ConductorPartTable(contains(ConductorPartTable.Name,'Slot1'),:);
% % firstSlotWirePartsTable =getFirstSlotWirePartTableFromPartStruct(PartStruct);  %% 외측 conductor확인
% ConductorNumber           =CoilWindingInfo.SlotLayerNumber;
% % Region Setting
% % Slot Poles 셋팅하는게 문제 있으니까 아예 스터디 템플렛을 Wire가 포함된걸로 저장
% setWireRegion(app,firstSlotWirePartsTable,ConductorNumber) 
%% Set Magnet Conductor  
% setMagnetConductor(app, MagnetTable, 1)
%% Condition Setting
setJMAGMotorConditions(app, PartStructByType, isConductor)
%% Winding Setting
% getCoilTable

txtFileList                             =findTXTFiles(refDIR)';
windingPatternTxtPath                   =txtFileList(contains(txtFileList,'Winding'));
[coilsTablePerCoil,CSVTab,outputPath]   = convertMCADPatternTable2JMAGCoilTable(windingPatternTxtPath{:});
% [WIP]CoilsTable Setting
%% WindingSettingObj Setting
importJMAGCoilsFromCSV(outputPath)
WindingObj=curStudyObj.GetWinding(0);
WindingObj.SetSerialGroups(width(coilsTablePerCoil))
WindingObj.SetComponent("Winding Three Phase Conductor1")
WindingObj.SetPhaseOrder("UWV")
% devsetJMAGWindingCoilsTable(coilTable,app)
%% mesh Condition
MeshCondtionTable = setupMotorMesh(app,PartStructByType); % defaulst Mesh Size

%% Copy Noload2>Load
NoLoadStudyName=[ModelName,'_NoLoad'];
LoadStudyName  =[ModelName,'_Load'];
PWMStudyName   =[ModelName,'_PWM'];
NumStudies=ModelObj.NumStudies;
while NumStudies<3
        % CurrentStudyName=c.GetStudy(NoLoadStudyName);
        % app.SetCurrentStudy(CurrentStudyName)
        % if ~strcmp(CurrentStudyName,LoadStudyName) 
        LoadStudyObj=ModelObj.GetStudy(LoadStudyName);
        if ~LoadStudyObj.IsValid
        ModelObj.DuplicateStudyName(NoLoadStudyName, LoadStudyName, true)        
        end
        PWMStudyObj=ModelObj.GetStudy(PWMStudyName);
        if ~PWMStudyObj.IsValid
        ModelObj.DuplicateStudyName(NoLoadStudyName, PWMStudyName, true)
        end
        NumStudies=ModelObj.NumStudies;
end
%% Circuit 
InputCurrentData.Current=RMSCurrent*sqrt(2);
InputCurrentData.freqE='FreqE';
InputCurrentData.phaseAdvance='MCADPhaseAdvance';
InputCurrentData.CoilList       = [1,5,13,9]; % TD
InputCurrentData.ParallelNumber = width(coilsTablePerCoil);
for StudyIndex=1:NumStudies
    curStudyObj=ModelObj.GetStudy(StudyIndex-1);
    app.SetCurrentStudy(curStudyObj.GetName)
    % No Load & Load    
    curStudyName=curStudyObj.GetName;
    if strcmp(NoLoadStudyName,curStudyName) |strcmp(LoadStudyName,curStudyName)
    CoilList            =InputCurrentData.CoilList;  
    setInsertInput2SinCircuit(app,InputCurrentData)
    % PWM
    elseif strcmp(PWMStudyName,curStudyName)
    loadJMAG_PWMInput(app)
    curStudyObj.GetCircuit().GetComponent("theta_m").SetLink("Rotation")
    end
end
%% Study Prop
for StudyIndex=1:NumStudies
    curStudyObj=ModelObj.GetStudy(StudyIndex-1);
    app.SetCurrentStudy(curStudyObj)
    StudyName=curStudyObj.GetName;
    %% LoadObj
    % NoLoadObj
    if contains(NoLoadStudyName,StudyName)
    StepDivision=120;
    elseif contains(LoadStudyName,StudyName)
    StepDivision=120;
    elseif contains(PWMStudyName,StudyName)
    StepDivision=1080;   % PWMOBJ
    end
    %%
    curStudyObj.GetStudyProperties().SetValue('ModelThickness', MachineData.Stator_Lam_Length)
    curStudyObj.GetStudyProperties().SetValue('NonlinearMaxIteration', 50)
    curStudyObj.GetStudyProperties().SetValue('NonlinearSpeedup', 0)
    curStudyObj.GetStudyProperties().SetValue('UseMultiCPU', 1)
    curStudyObj.GetStudyProperties().SetValue('MultiCPU', 4) 
    curStudyObj.GetStep().SetValue("StepType", 1)
    curStudyObj.GetStep().SetValue("Step", 4*StepDivision+1)
    curStudyObj.GetStep().SetValue("StepDivision", StepDivision)
    curStudyObj.GetStep().SetValue("EndPoint", "1/FreqE")
end

%% StudyPropertiesTable
% Model=app.GetCurrentModel;
propertiesTableWithValue=getJMagStudyProperties(curStudyObj);
app.Save

%% DesignTable
curStudyObj

curStudyObj.GetDesignTable().AddCases(8)
DTObj=curStudyObj.GetDesignTable();
for CaseIndex=1:8
    DTObj.SetValue(CaseIndex,'speed',speedList{CaseIndex-1})
end



%% submit 
    app.SetProjectName('e10');    
    ProjectName=app.GetProjectName;
    ProjectPath=app.GetProjectPath;
ModelObj=app.GetCurrentModel;
for StudyIndex=1:NumStudies
    curStudyObj=ModelObj.GetStudy(StudyIndex-1);
    app.SetCurrentStudy(curStudyObj.GetName)
    ModelName=ModelObj.GetName;
    StudyName=curStudyObj.GetName();
    jobData =curStudyObj.CreateJob();
    if jobData.IsValid
    jobData.SetValue("Title", [ProjectName,ModelName,StudyName,num2str(StudyIndex)]);
    jobData.SetValue("Queued", 1);
    jobData.Submit(true);
    end
end

%% load result
% waveform
% field result
LossStudyResultTableObj=curStudyObj.GetResultTable;
ResultDataStruct       = getJMagResultDatas(LossStudyResultTableObj,'voltage');



% Joule Loss [W]

%% get ResultTable Obj
app=       callJmag
ModelObj=app.GetCurrentModel
StudyIndex=4
curStudyObj=ModelObj.GetStudy(StudyIndex-1)
LossStudyResultTableObj=curStudyObj.GetResultTable
% get DataStruct
ResultDataStruct  = getJMagResultDatas(LossStudyResultTableObj,'voltage')
currentDataStruct = getJMagResultDatas(LossStudyResultTableObj,'current')
jouleDataStruct   = getJMagResultDatas(LossStudyResultTableObj,'Joule')

%% select conductor name
list=jouleDataStruct(1).dataTable.Properties.VariableNames'
u1List=contains(jouleDataStruct(1).dataTable.Properties.VariableNames,'Slot1')

% DC Loss  [W]
% Current * Resistance
activePhaseResistance=MachineData.ResistanceActivePart

%% Compare with Coil Post Calculation
ModelObj=app.GetCurrentModel
NumStudies=ModelObj.NumStudies;
PJTPDir=app.GetProjectFolderPath();
ModelObj.GetStudy
ModelName=ModelObj.GetName;
if ~contains(ModelName,'ref_','IgnoreCase',true)&contains(ModelName,'sc_','IgnoreCase',true)
    ModelObj.SetName(['ref_',ModelName])
end
ModelName=ModelObj.GetName;

%% Study 이름에 Model이름과 Noload인지 Load인지 붙이기 
NumModels=app.NumModels;
for modelIndex=1:NumModels
    tempModelObj    =app.GetModel(int32(modelIndex)-1);
    tempModelName   =tempModelObj.GetName;
    NumStudies      =tempModelObj.NumStudies;
    if tempModelObj.IsValid
        for studyIndex=1:NumStudies
          tempStudyObj=tempModelObj.GetStudy(int32(studyIndex)-1);
          tempStudyName   =tempStudyObj.GetName;
          if contains(tempStudyName,'NoLoad','IgnoreCase',true)
              tempStudyObj.SetName([tempModelName,'_NoLoad'])
          elseif contains(tempStudyName,'_Load','IgnoreCase',true)
              tempStudyObj.SetName([tempModelName,'_Load']);
          else
              tempStudyObj.SetName([tempModelName,tempStudyName]);
          end
        end
    end
end

%% scaling
%% skin Depth Model
delta=calcSkinDepth(omega2freq(rpm2OmegaE(1000,4))) % 2.25594 -;

AppNumStudies=app.NumStudies
for AppStudyIndex=1:AppNumStudies
    curAppStudyObj=app.GetStudy(AppStudyIndex-1);
    MeshConObj    =curAppStudyObj.GetMeshControl;
    MeshConObj.CreateCondition("RotationPeriodicMeshAutomatic", "RPMesh")
end
%% Mk scale
mkJMAGScaling(app,RadialscaleFactor)

%% Scaling후 전체 Table
%% RDP포트번호 추출
[status, cmdout] = system('reg query "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" /v PortNumber');
if status == 0
    % Extract the port number from the output
    portNumberStr = regexp(cmdout, 'PortNumber\s+REG_DWORD\s+(\w+)', 'tokens', 'once');
    portNumber = hex2dec(portNumberStr{1});
    fprintf('RDP Port Number: %d\n', portNumber);
else
    fprintf('Failed to query the registry.\n');
end

PJTName=app.GetProjectName;
% CurrentFilePath =mfilename("fullpath");
CurrentFilePath='D:\KangDH\Emlab_emach\mlxperPJT\JEET\e10MQS_WireTemplate_38100.m';
AppNumStudies=app.NumStudies
[MfileDir,~,~]  =fileparts(CurrentFilePath )
for AppStudyIndex=1:AppNumStudies
    curStudyObj=app.GetStudy(int32(AppStudyIndex)-1);
    StudyName=curStudyObj.GetName;
    RTableObj=curStudyObj.GetResultTable;
    if RTableObj.IsValid
        NumTables=RTableObj.NumTables;
        ResultFilePath{AppStudyIndex} =fullfile([PJTName,StudyName,'_port',num2str(portNumber),'.csv']);
        RTableObj.WriteAllCaseTables(fullfile(MfileDir,ResultFilePath{AppStudyIndex}),'Steps')
    end
end

%% 이건 dev10_JMAG에서실행 Table가져오기 - study이름에 이미포함되어있어서 상관없구나
% D:\KangDH\Emlab_emach\mlxperPJT\JEET\deve10_JMAG_MQS_ACLoss.m
for AppStudyIndex=1:AppNumStudies
    opts=delimitedTextImportOptions('NumVariables',2000);
    if exist(ResultFilePath{AppStudyIndex},"file")
    resultTableCell{AppStudyIndex,1}=readtable(ResultFilePath{AppStudyIndex},opts);
    resultTableCell{AppStudyIndex,2}=ResultFilePath{AppStudyIndex};
    end
end

%%  Get All Data
TablesCellCaseRowDataCol = parseJMAGResultTable(resultTableCell{AppStudyIndex,1});
TablesCellCaseRowDataCol.Properties.Description=resultTableCell{AppStudyIndex,2};
%%
