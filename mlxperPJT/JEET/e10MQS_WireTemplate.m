%% dev 
% % Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\deve10MQSplotAC.m에서 활용
% Circuit 생성 어떻게 할지 결정

%% from
%  devJmagSettingwithConductor
% Z:\01_Codes_Projects\git_fork_emach\tools\jmag\devJmagWindingSetting.mlx
%% MCAD
% in origin MLX 
%%% ***** 먼저 실행 JEETResult_rev1.mlx

% 이 파일은 JMAG Jproj 호출을 위한 m파일입니다
%% rev1에서 회전자 dxf 수정함
refPath='Z:\Simulation\JEETACLossValid_e10_v24\refModel\';
dxfFiles = findDXFFiles('Z:\Simulation\JEETACLossValid_e10_v24\refModel')';
%% JMAG
app=callJmag;
app.Show
jprojFiles=app.GetProjectFolderPath;
jprojPath='Z:\Simulation\JEETACLossValid_e10_v24\JMAG\e10_JFT145_WireTemp.jproj';
if ~exist(jprojPath,"file")
app.SaveAs(jprojPath)
end

app.Load(jprojPath)
Model=app.GetCurrentModel;
jprojFiles=app.GetProjectFolderPath;

% Model.SetStudyOrder("NoLoad", 0)
%% 
StepDivision=120;
EndTime=1/FreqE;
%% Import
% dxfList2Import=defDXFList2Import(dxfFiles, 5,3);
DXFMatFilePath=fullfile(jprojFiles,'ImportDXF.mat');
if ~exist(DXFMatFilePath,"file")
    save(DXFMatFilePath,'dxfList2Import');
else
    load(DXFMatFilePath);
end
Model=app.GetCurrentModel;
Model.RestoreCadLink()
geomApp=app.CreateGeometryEditor(0);

% Check Exist Assem N Import
AssemTable = getGeomAssemItemListTable(geomApp);

delete2AssemInJMAG= 'Rotor';
delete2AssemInJMAG=[];
if exist('AssemTable',"var")&~isempty(delete2AssemInJMAG)
    delete2AssemTable=AssemTable(contains(AssemTable.AssemItemName,delete2AssemInJMAG),:);
    if isempty(AssemTable)
    sketchs=ImportDXF2Geom(dxfList2Import,geomApp);
    else 
    geomApp.GetDocument().GetSelection().Add(delete2AssemTable.AssemItem);
    geomApp.GetDocument().GetSelection().Delete()
    dxfList2Import=dxfList2Import(contains(dxfList2Import.sketchName,delete2AssemInJMAG),:);
    sketchs=ImportDXF2Geom(dxfList2Import,geomApp);
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
% geomApp.GetDocument().GetAssembly().GetItem("Rotor").OpenSketch()
% geomApp.GetDocument().GetAssembly().GetItem("Rotor").GetItem("Shaft").SetProperty("Suppress", 1)
% geomApp.GetDocument().GetAssembly().GetItem("Rotor").CloseSketch()
%
RotorRegionTablePerType = detRotorRegionTablePerType(RotorAssemRegionTable);
StatorRegionTablePerType = detStatorRegionTablePerType(StatorAssemRegionTable);

%%% Arc 
StatorGeomArcTable=getArcTable(StatorAssemRegionTable);
RotorGeomArcTable=getArcTable(RotorAssemRegionTable);
runnerType=checkInnerOuterMotor(StatorGeomArcTable,RotorGeomArcTable);
%% if no WireTemplate and ConductorTable is not Empty
% Import Stator Taemplate and Delete exist Stator Assem

jmdlFileName='JFT145Stator_geomTemplate';
filePathCell=findFilePaths(jmdlFileName,fileparts(jprojFiles));
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
    geomApp.GetDocument().GetSelection().Add(geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName))
    geomApp.GetDocument().GetSelection().Delete()
      %% merge 
    geomApp.MergeJmdl(jmdlfilePath)
    preAssembleName="StatorWithTemplate";
    StatorObj=geomApp.GetDocument().GetAssembly().GetItem(preAssembleName);
    StatorObj.SetName('Stator');
    %% Wire Template Coincident
    ref1 = geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).GetItem("Line.6")
    ref2 = geomApp.GetDocument().CreateReferenceFromItem(ref1)
    ref3 = geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).GetItem("Line")
    ref4 = geomApp.GetDocument().CreateReferenceFromItem(ref3)
    geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).CreateBiConstraint("coincident", ref2, ref4)
    geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("RectangleWidth", 1.6)
    geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("RectangleHeight", 3.7)
    geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("WireCoatingThickness", 0.1)
    geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("WieGapDistance", 0.15)
    geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("WireCount", 4)
    geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("FillFactor", 63.8825526278559)
    geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("StartDeltaX", 5)
    geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).GetItem("Wire Template").SetProperty("StartDeltaY", "5*tan(3.75*pi/180)")
    
    %% set Geom Contraint
    SW4Obj=StatorObj.GetItem('SW4');
    SW4Obj.IsValid
    SW4Obj.SetDistance(BackyokeLength)
    geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).GetItem("SD1").SetProperty("Diameter", SOD)
    geomApp.GetDocument().GetAssembly().GetItem(StatorGeoAssemName).GetItem("SD4").SetProperty("Diameter", SID)
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
    createCircPattern4withInput(StatorAssemRegionTable,'',geomApp)
    end
elseif isempty(AssemTable)
    getGeomMagnetizationEdgeSet(RotorAssemRegionTable,geomApp);
end
%% Import 
app.ImportDataFromGeometryEditor();
%% Designer ModelObj
Model=app.GetCurrentModel;
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
    ConductorModelObj=Model;
    ConductorMeshSize=0.5;
elseif isConductor==2
    ModelName='e10_WireTemplate';
    ConductorModelObj=Model;
    ConductorMeshSize=0.5;
else
    ModelName='e10_Coil';
    CoilModelObj=Model;
    ConductorMeshSize=1;
end

Model.SetName(ModelName)
ModelName=Model.GetName;
app.SetCurrentModel(ModelName)


%% ungroup
rmJModelAllGroups(app)
% oldFileName='writeJmagWindingPatternCSV'
% newFileName='devWriteJmagWindingPatternCSV'
% renameFile(newFileName,oldFileName)
%% Model PartName Change & Model Set - PartStruct
PartStruct          =getJMAGDesignerPartStruct(app);
PartTable           =struct2table(PartStruct);
% stator CoreName
changeJMAGPartNameTable(PartStructByType.StatorCoreTable,app)
%% reGet
PartStruct          =getJMAGDesignerPartStruct(app);
PartStructByType    =convertJmagPartStructByType(PartStruct);
PartStructByType    = convertJmagPartStructByType(PartStruct);
PartStructByType.SlotTable.Name=strrep(PartStructByType.SlotTable.Name,'StatorWithTemplate','Stator');
%% Magnet
sortedMagnetTables = sortMagnetTableByNumber(PartStructByType);
%% Conductor Table
if isConductor>0 & isempty(PartStructByType.ConductorTable)
PartStructByType.ConductorTable=PartStructByType.SlotTable;
PartStructByType.SlotTable=0;
end
%%[TC] add LayerNumber sortingConductorTableBySlot
ConductorPartTable=sortingConductorTableBySlot(PartStructByType.ConductorTable,app);

%% reGet
PartStruct=getJMAGDesignerPartStruct(app);
PartStructByType = convertJmagPartStructByType(PartStruct);
if isConductor>0 & isempty(PartStructByType.ConductorTable)
PartStructByType.ConductorTable=PartStructByType.SlotTable;
PartStructByType.SlotTable=0;
end
%% Change Name
Model=app.GetCurrentModel;
Model.SortPartsByName()
%% Make Set
SlotConductorSetName="SlotConductor";

strcell=strsplit(PartStructByType.ConductorTable.Name{1},'/');
SetObj=Model.GetSetList.GetSet(SlotConductorSetName);
if ~(SetObj.IsValid)
Model.GetSetList().CreatePartSet(SlotConductorSetName)
Model.GetSetList().GetSet(SlotConductorSetName).SetUpdateByRelation(false)
Model.GetSetList().GetSet(SlotConductorSetName).SetMatcherType("MatchNames")
Model.GetSetList().GetSet(SlotConductorSetName).SetParameter("style", "prefix")
Model.GetSetList().GetSet(SlotConductorSetName).SetParameter("text", [strcell{1},"/Slot"])
Model.GetSetList().GetSet(SlotConductorSetName).Rebuild()
end
RotorSetName="Rotor";
SetObj=Model.GetSetList.GetSet(RotorSetName);
if ~(SetObj.IsValid)
Model.GetSetList().CreatePartSet(RotorSetName)
Model.GetSetList().GetSet(RotorSetName).SetMatcherType("MatchNames")
Model.GetSetList().GetSet(RotorSetName).SetParameter("style", "prefix")
Model.GetSetList().GetSet(RotorSetName).SetParameter("text", "Rotor")
Model.GetSetList().GetSet(RotorSetName).Rebuild()
end
%% createStudy or apply Template
useTemplate=1;
TemplateName='IPMSM_WireSinCond';

NumModels=app.NumModels;

for ModelIndex=1:NumModels
    Model=app.GetModel(ModelIndex-1);
    NumStudies=Model.NumStudies;
    if NumStudies==0
        if useTemplate==0
            for StudyIndex=1:1
            StudyNameList={'NoLoad'};
            StudyObj=Model.CreateStudy('Transient2D',[ModelName,StudyNameList{StudyIndex}]);
            end
        elseif useTemplate==1
            ApplyJMAGAnalysisTemplate(TemplateName,app)
        end
    else
        disp('manual')
        NoloadStudyObj=Model.GetStudy(0);
        NoloadStudyObj.GetName;
        NoloadStudyObj.SetName([ModelName,'_NoLoad'])
        loadStudyObj=Model.GetStudy(1);
        loadStudyObj.GetName
        loadStudyObj.SetName([ModelName,'_Load'])
    end
end


%% [TC] Copy Noload2>Load
ModelName=app.GetCurrentModel.GetName;
NoLoadStudyName=[ModelName,'_NoLoad'];
LoadStudyName  =[ModelName,'_Load'];
PWMStudyName   =[ModelName,'_PWM'];
NumStudies=Model.NumStudies;
while NumStudies<3
        % CurrentStudyName=Model.GetStudy(NoLoadStudyName);
        % app.SetCurrentStudy(CurrentStudyName)
        % if ~strcmp(CurrentStudyName,LoadStudyName) 
        LoadStudyObj=Model.GetStudy(LoadStudyName);
        if ~LoadStudyObj.IsValid
        Model.DuplicateStudyName(NoLoadStudyName, LoadStudyName, true)        
        end
        PWMStudyObj=Model.GetStudy(PWMStudyName);
        if ~PWMStudyObj.IsValid
        Model.DuplicateStudyName(NoLoadStudyName, PWMStudyName, true)
        end
        NumStudies=Model.NumStudies;
end

NumStudies=Model.NumStudies;
while NumStudies<3
        % CurrentStudyName=Model.GetStudy(NoLoadStudyName);
        % app.SetCurrentStudy(CurrentStudyName)
        % if ~strcmp(CurrentStudyName,LoadStudyName) 
        LoadStudyObj=Model.GetStudy(LoadStudyName);
        if ~LoadStudyObj.IsValid
        Model.DuplicateStudyName(NoLoadStudyName, LoadStudyName, true)        
        end
        PWMStudyObj=Model.GetStudy(PWMStudyName);
        if ~PWMStudyObj.IsValid
        Model.DuplicateStudyName(NoLoadStudyName, PWMStudyName, true)
        end
        NumStudies=Model.NumStudies;
end
app.Save


NumModels=app.NumModels;
for ModelIndex=1:NumModels
    Model=app.GetModel(ModelIndex-1);
    NumStudies=Model.NumStudies;
    %% Material Set
    BandMaterial                ='Air'                  ;
    ShaftMaterial               ='Air'                  ;
    RotorCoreMaterial           ="NO18-1160"     ;    
    MagNetMaterial              ="N42EH"         ;
    MagnetTable=PartStructByType.MagnetTable;
    NumStudies=Model.NumStudies;
    for StudyIndex=1:NumStudies
        curStudyObj=Model.GetStudy(StudyIndex-1);
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
    curStudyObj=Model.GetStudy(StudyIndex-1);
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
txtFileList                             =findTXTFiles('Z:\Simulation\JEETACLossValid_e10_v24\refModel')';
windingPatternTxtPath                   =txtFileList(contains(txtFileList,'turn'));
[coilsTablePerCoil,CSVTab,outputPath] = convertMCADPatternTable2JMAGCoilTable(windingPatternTxtPath{:});
% [WIP]CoilsTable Setting
%% WindingSettingObj Setting
importJMAGCoilsFromCSV(outputPath)
% devsetJMAGWindingCoilsTable(coilTable,app)
%% Circuit 
InputCurrentData.Current=RMSCurrent*sqrt(2);
InputCurrentData.freqE='FreqE';
InputCurrentData.phaseAdvance='MCADPhaseAdvance';
InputCurrentData.CoilList       = [1,5,13,9]; % TD
InputCurrentData.ParallelNumber = width(coilTable)
NoLoadStudyName=[ModelName,'_NoLoad'];
LoadStudyName  =[ModelName,'_Load'];
PWMStudyName   =[ModelName,'_PWM'];

for StudyIndex=1:NumStudies
    curStudyObj=Model.GetStudy(StudyIndex-1);
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
%% mesh
% Mesh Condition

for StudyIndex=1:NumStudies
    curStudyObj=Model.GetStudy(StudyIndex-1);
    app.SetCurrentStudy(curStudyObj)
    % 2.8 Mesh Seting
    % MeshControlObj 
    MeshControlObj=curStudyObj.GetMeshControl();
    % General Properties
    MeshControlObj.SetValue("MeshType", 1)
    MeshControlObj.SetValue("AirRegionDirection", 1)
    MeshControlObj.SetValue("AirRegionScaleY", 1.15)
    %% skinDepth
    omegaE=rpm2OmegaE(rpm,4);
    SkinDepth_delta_inmm = calcSkinDepth(omegaE);
    MeshControlObj=curStudyObj.GetMeshControl();
    if MeshControlObj.GetCondition('ConductorSkinDepth').IsValid
        ConductorSkinDepthObj=MeshControlObj.GetCondition("ConductorSkinDepth");
    else
            ConductorSkinDepthObj=MeshControlObj.CreateCondition("SkinDepth", "ConductorSkinDepth");
    end
    ConductorSkinDepthObj.SetValue("Depth", 0.4)
    ConductorSkinDepthObj.SetValue("Division", 2)
    ConductorSkinDepthObj.SetValue("CommonRatio", 1)
    ConductorSkinDepthObj.ClearParts()
    ConductorSkinDepthObj.AddSetFromModel(SlotConductorSetName,0)

    % Conductor
    ConductorMeshPartObj=curStudyObj.CreateCondition("Part", "ConductorPart"); 
    ConductorMeshPartObj.SetValue("Size", ConductorMeshSize)
    ConductorMeshPartObj.ClearParts()
    ConductorMeshPartObj.AddSetFromModel(SlotConductorSetName,0)
    % core
    coreMeshPartObj=MeshControlObj.CreateCondition("Part", "CorePart");
    coreMeshPartObj.SetValue("Size",0.5)
    coreMeshPartObj.ClearParts()
    coreMeshPartObj.AddPart("Stator/StatorCore")
    coreMeshPartObj.AddPart("Rotor/RotorCore")
    
    % Magnet
    MagnetMeshPartObj=MeshControlObj.CreateCondition("Part", "MagnetPart");
    MagnetMeshPartObj.SetValue("Size",1)
    MagnetMeshPartObj.ClearParts()
    
    %MagnetTable
    for MagnetIndex=1:height(MagnetTable)
    MagnetMeshPartObj.AddPart(MagnetTable.Name{MagnetIndex})
    end

    %meshTotalPropertyTable
    meshTotalPropertyTable=MeshControlObj.GetPropertyTable;
    meshTotalPropertyTable=char2CategoricalPropertiesTable(meshTotalPropertyTable);
    
    % MeshControl Condition
    NumConditions=MeshControlObj.NumConditions   ;
    MeshCondtionTable=table();
    for MeshConditionIndex=1:NumConditions
    MeshCondtionObj=MeshControlObj.GetCondition(MeshConditionIndex-1);
    MeshCondtionTable.MeshCondition(MeshConditionIndex)             =MeshCondtionObj;
    MeshCondtionTable.CondtionType{MeshConditionIndex}              ={MeshCondtionObj.GetType};
    MeshCondtionTable.Name{MeshConditionIndex}                      ={MeshCondtionObj.GetName};
    MeshCondtionTable.MeshCondtionPropertyTable(MeshConditionIndex) ={char2CategoricalPropertiesTable(MeshCondtionObj.GetPropertyTable)};
    MeshCondtionTable.Parts(MeshConditionIndex)                     ={MeshCondtionObj.GetParts};
    end
end

%% Study Prop

for StudyIndex=1:NumStudies
    curStudyObj=Model.GetStudy(StudyIndex-1);
    app.SetCurrentStudy(curStudyObj)
    StudyName=curStudyObj.GetName;
    %% LoadObj
    % NoLoadObj
    if strcmp(NoLoadStudyName,StudyName)
    StepDivision=120;
    elseif strcmp(LoadStudyName,StudyName)
    StepDivision=120;
    elseif strcmp(PWMStudyName,StudyName)
    StepDivision=1080;   % PWMOBJ
    end
    %%
    curStudyObj.GetStudyProperties().SetValue('ModelThickness', MachineData.Stator_Lam_Length)
    curStudyObj.GetStudyProperties().SetValue('NonlinearMaxIteration', 50)
    curStudyObj.GetStudyProperties().SetValue('NonlinearSpeedup', 0)
    curStudyObj.GetStudyProperties().SetValue('UseMultiCPU', 1)
    curStudyObj.GetStudyProperties().SetValue('MultiCPU', 4) 
    curStudyObj.GetStep().SetValue("Step", 4*StepDivision+1)
    curStudyObj.GetStep().SetValue("StepType", 1)
    curStudyObj.GetStep().SetValue("StepDivision", StepDivision)
    curStudyObj.GetStep().SetValue("EndPoint", "1/ FreqE")
end

%% StudyPropertiesTable
% Model=app.GetCurrentModel;
propertiesTableWithValue=getJMagStudyProperties(curStudyObj);
%% submit 
    app.SetProjectName('e10');    
    ProjectName=app.GetProjectName;
    ProjectPath=app.GetProjectPath;

Model=app.GetCurrentModel
for StudyIndex=1:NumStudies
    curStudyObj=Model.GetStudy(StudyIndex-1);
    app.SetCurrentStudy(curStudyObj.GetName)
    ModelName=Model.GetName;
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
LossStudyResultTableObj=curStudyObj.GetResultTable
ResultDataStruct       = getJMagResultDatas(LossStudyResultTableObj,'voltage')


% Joule Loss [W]

%% get ResultTable Obj
app=callJmag
Model=app.GetCurrentModel
StudyIndex=4
curStudyObj=Model.GetStudy(StudyIndex-1)
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
