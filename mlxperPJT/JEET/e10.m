%% MCAD
% in origin MLX 
% JEETResult_rev1.mlx

% 이 파일은 JMAG Jproj 호출을 위한 m파일입니다
%% rev1에서 회전자 dxf 수정함

refPath='Z:\Simulation\JEETACLossValid_e10_v24\refModel\';
dxfFiles = findDXFFiles('Z:\Simulation\JEETACLossValid_e10_v24\refModel')';
entitiesRotorStruct = readDXF(dxfFiles{1});
entitiesRotorStruct = arrayfun(@(x) setfield(x, 'layer', 'rotor'), entitiesRotorStruct);
RotorDxf = filterEntitiesByAngle(entitiesRotorStruct, 22.5);
plotEntitiesStruct(RotorDxf)
NewtestRotorDXFPath=strsplit(dxfFiles{1},'.');
NewtestRotorDXFPath=[NewtestRotorDXFPath{1},'Periodic','.dxf'];
delete(NewtestRotorDXFPath)
writeDXF(NewtestRotorDXFPath, RotorDxf);

%% JMAG
app=callJmag;
app.Show
app.GetProjectFolderPath
jprojPath='Z:\Simulation\JEETACLossValid_e10_v24\JMAG\MCADv24e10_refModel2_JMAG_JFT047.jproj';
app.Load(jprojPath)
Model=app.GetCurrentModel;
% Model.SetStudyOrder("NoLoad", 0)
%% 
StepDivision=120;
EndTime=1/FreqE;

%% Import
dxfList2Import=defDXFList2Import(dxfFiles, 4,2);
Model=app.GetCurrentModel;
Model.RestoreCadLink()
geomApp=app.CreateGeometryEditor(0);

% Check Exist Assem
AssemTable = getGeomAssemItemListTable(geomApp);

delete2AssemInJMAG= 'Rotor';
delete2AssemTable=AssemTable(contains(AssemTable.AssemItemName,delete2AssemInJMAG),:);
if isempty(AssemTable)
sketchs=ImportDXF2Geom(dxfList2Import,geomApp);
else 
geomApp.GetDocument().GetSelection().Add(delete2AssemTable.AssemItem);
geomApp.GetDocument().GetSelection().Delete()
dxfList2Import=dxfList2Import(contains(dxfList2Import.sketchName,delete2AssemInJMAG),:);
sketchs=ImportDXF2Geom(dxfList2Import,geomApp);
end

%% setGet GeomAssemTable 
StatorAssemRegionTable=setGetGeomStatorNameNTable(geomApp);
RotorAssemRegionTable =setGetGeomRotorNameNTableInnerRotor(geomApp);

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


%% 자석 edge잡기 & Stator Pattern
if contains(delete2AssemInJMAG, 'Rotor')
getGeomMagnetizationEdgeSet(RotorAssemRegionTable,geomApp);
elseif contains(delete2AssemInJMAG, 'Stator')
% Stator pattern
createCircPattern4withInput(StatorAssemRegionTable,'',geomApp)
end

%% GeomDesginTable
% [Skip] GeomDesginTable
setGeomDesignTable('stack_length',MachineData.Stator_Lam_Length,app);
% setGeomDesignTable('Freq',Freq,app);
setGeomDesignTable('SLOTS',MachineData.Slot_Number,app);
setGeomDesignTable('POLES',MachineData.Pole_Number,app);
app.ImportDataFromGeometryEditor();
%% Designer ModelObj
Model=app.GetCurrentModel;
isConductor=1;
if isConductor==1
    ModelName='e10_Conductor';
    ConductorModelObj=Model;
    ConductorMeshSize=0.5;
else
    ModelName='e10_Coil';
    CoilModelObj=Model;
    ConductorMeshSize=1;
end

Model.SetName(ModelName)

NumStudies=Model.NumStudies;
ModelName=Model.GetName;

%% Model PartName Change & Model Set - PartStruct
PartStruct=getJMAGDesignerPartStruct(app);
PartTable=struct2table(PartStruct);
PartStructByType = convertJmagPartStructByType(PartStruct);
sortedMagnetTables = sortMagnetTableByNumber(PartStructByType);
ConductorPartTable=sortingConductorTableBySlot(PartStruct);
%% Change Name
changeJMAGPartNameTable(ConductorPartTable,app);
PartStructByType = convertJmagPartStructByType(PartStruct);
if isconductor==1
PartStructByType.ConductorTable=PartStructByType.SlotTable;
PartStructByType.SlotTable=0;
end

% Make Set
SlotConductorSetName="SlotConductor";
SetObj=Model.GetSetList.GetSet(SlotConductorSetName);
if ~(SetObj.IsValid)
Model.GetSetList().CreatePartSet(SlotConductorSetName)
Model.GetSetList().GetSet(SlotConductorSetName).SetUpdateByRelation(false)
Model.GetSetList().GetSet(SlotConductorSetName).SetMatcherType("MatchNames")
Model.GetSetList().GetSet(SlotConductorSetName).SetParameter("style", "prefix")
Model.GetSetList().GetSet(SlotConductorSetName).SetParameter("text", "Stator/Slot")
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

if NumStudies==0
    if useTemplate==0
        for StudyIndex=1:2
        StudyNameList={'NoLoad','Load'};
        StudyObj=Model.CreateStudy('Transient2D',[ModelName,StudyNameList{StudyIndex}]);
        end
    else
    disp('manual')
    end
else
    NoloadStudyObj=Model.GetStudy(0);
    NoloadStudyObj.GetName;
    NoloadStudyObj.SetName([ModelName,'_NoLoad'])
    loadStudyObj=Model.GetStudy(1);
    loadStudyObj.GetName
    loadStudyObj.SetName([ModelName,'_Load'])
end



%% Copy Noload2>Load
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
%% Material Set
BandMaterial                ='Air'                  ;
ShaftMaterial               ='Air'                  ;
RotorCoreMaterial           ="NO18-1160"     ;    
MagNetMaterial              ="N42EH"         ;
MagnetTable=PartStructByType.MagnetTable;

for StudyIndex=1:NumStudies
    curStudyObj=Model.GetStudy(StudyIndex-1);
    app.SetCurrentStudy(curStudyObj.GetName)
    setMagnetMagnetizationbyEdgeSet(app,MagNetMaterial,MagnetTable)
    curStudyObj.SetMaterialByName("Stator/StatorCore",RotorCoreMaterial)
    curStudyObj.SetMaterialByName("Rotor/RotorCore", RotorCoreMaterial)
    curStudyObj.SetMaterialByName("Band",BandMaterial)
    curStudyObj.SetMaterialByName("Shaft",ShaftMaterial)
end
% mkJmag3phaseCoilSinCircuit(app)
% R_phaseJMAG=devJmagPhaseResistanceFromWindingSet(CoilWindingInfo,app)

%% Set Magnet Conductor  
Model=app.GetCurrentModel;
MagnetNameIndex=find(contains(MagnetTable.Name,'magnet','IgnoreCase',true));
for MagnetIndex=1:height(MagnetNameIndex) 
    CurrentStudyObj=Model.GetStudy(StudyIndex-1);
    MagnetName=MagnetTable.Name{MagnetNameIndex(MagnetIndex)};   
    partIndex=MagnetTable.partIndex(MagnetIndex);
    % set Allow EddyCurrent
    CurrentStudyObj.GetMaterial(partIndex).SetValue("EddyCurrentCalculation", 1)
    % create circuit 
    magConductorName=['mag',num2str(MagnetIndex)];
    yPosition=0+5*MagnetIndex; 
    circuitObj=CurrentStudyObj.GetCircuit;
    ComponentObj=circuitObj.GetComponent(magConductorName);
    if ~ComponentObj.IsValid
    circuitObj.CreateComponent("FEMConductor", magConductorName)
    circuitObj.CreateInstance(magConductorName, -77, yPosition+63)
    circuitObj.CreateComponent("Ground", "Ground")
    circuitObj.CreateInstance("Ground", -75, yPosition+61)
    end
    % create Condition
    if ~CurrentStudyObj.GetCondition(magConductorName).IsValid
    curConditionObj=CurrentStudyObj.CreateCondition("FEMConductor",magConductorName);
    % Link Magnet
    curConditionObj.SetLink(magConductorName)
    curConditionObj.GetName
    curConditionObj.NumSubConditions
    % select Part
    subConObj=curConditionObj.GetSubCondition(0);
    subConObj.IsValid
    subConObj.GetName
    subConObj.ClearParts()
    sel = subConObj.GetSelection();
    sel.SelectPart(partIndex);
    subConObj.AddSelected(sel)
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

Model=app.GetCurrentModel;
Model.GetName
%% Circuit 
for StudyIndex=1:NumStudies
    curStudyObj=Model.GetStudy(StudyIndex-1);
    app.SetCurrentStudy(curStudyObj.GetName)
    InputCurrentData.Current=RMSCurrent*sqrt(2);
    InputCurrentData.freqE='FreqE';
    InputCurrentData.phaseAdvance='MCADPhaseAdvance';
    % No Load & Load    
    curStudyName=curStudyObj.GetName;
    if strcmp(NoLoadStudyName,curStudyName) |strcmp(LoadStudyName,curStudyName)
    setInsertInput2SinCircuit(app,InputCurrentData)
    % PWM
    elseif strcmp(PWMStudyName,curStudyName)
    loadJMAG_PWMInput(app)
    curStudyObj.GetCircuit().GetComponent("theta_m").SetLink("Rotation")
    end
end

%% Condition Setting
% 중복 생성 방지
Model=app.GetCurrentModel;
for StudyIndex=1:NumStudies
    curStudyObj=Model.GetStudy(StudyIndex-1);
    app.SetCurrentStudy(curStudyObj)
    Dtable=curStudyObj.GetDesignTable();
    Pole=Dtable.GetEquation('POLES').GetValue;
    Slot=Dtable.GetEquation('SLOTS').GetValue;
    RotorOnePoleAngle=calcMotorPeriodicity(Pole,Slot);
    % RotorOnePoleAngle=max(RotorGeomArcTable.EndVertexTabletheta);
    StatorEdgeXposition =StatorAssemRegionTable.distanceRFromCenter(1)/2;
    %  2.7.1 Rotationaly Periodic Boundary
    setRPBoundaryCondition(curStudyObj,RotorOnePoleAngle ,StatorEdgeXposition);
    % 2.7.2 Motion
    setRotationMotion(curStudyObj,'speed/60')
    % 2.7.4 torque
    setTorqueCondition(curStudyObj);
    % 2.7.3 Coil or Conductor
    if ~isempty(PartStructByType.SlotTable) & isConductor==0      
        setJMAGFEMCoil(curStudyObj,PartStructByType)                
    elseif isempty(PartStructByType.SlotTable)& ~isempty(PartStructByType.ConductorTable)
        setJMAGFEMConductor(ConductorPartTable,curStudyObj)
        for PartIndex=1:height(ConductorPartTable)
        curStudyObj.SetMaterialByName(ConductorPartTable.Name{PartIndex},"Copper")
        curStudyObj.GetMaterial(ConductorPartTable.Name{PartIndex}).SetValue("EddyCurrentCalculation", 1)
        end
        % mesh
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
    end
end

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

NoLoadStudyName=[ModelName,'_NoLoad'];
LoadStudyName  =[ModelName,'_Load'];
PWMStudyName   =[ModelName,'_PWM'];
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
% 

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

%% StudyPropertiesTable
% Model=app.GetCurrentModel;
propertiesTableWithValue=getJMagStudyProperties(curStudyObj);
%% submit 
    app.SetProjectName('e10');    
    ProjectName=app.GetProjectName;
    ProjectPath=app.GetProjectPath;

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


%% Compare with Coil Post Calculation
