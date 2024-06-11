mcad=callMCAD
%% 경로
jprojPath="Z:\Simulation\JMAGDev\e10JFT047FeedbackControl.jproj"
InitialStudyName='FullPyFeedBackLoss'

%% 1. Model Setting -

% Should Use Template? - No? Why?
% Winding Setting Type - First, in the JFT047 fashion
% Model - MCADe10
% DXF Import - From devJmagSettingV4InnerRotorCheck
% Material - MCAD Material Making//
% File 새로 (1. 셋팅을 하나씩, 2. setting 정보를 mat으로 가지고 있다가 입력) or Setting File로부터?
% testDXFPath="Z:\Simulation\LabProj2023Evaluation\EqualFillFactor\A1_60"
testDXFPath='Z:\Simulation\JEETACLossValid_e10_v23\refModel'

%% Conductor
settingDXFTable=defMCADDXFExportSettingVariable('Stator');
testStatorDXFPath='Z:\Simulation\JEETACLossValid_e10_v23\refModel\e10_User_stator.dxf'
settingDXFTable.CurrentValue(contains(settingDXFTable.AutomationName,'FileName'))={testStatorDXFPath};
setMcadTableVariable(settingDXFTable,mcad)
mcad.GeometryExport()

%% Rotor

settingDXFTable=defMCADDXFExportSettingVariable('Rotor');
testRotorDXFPath='Z:\Simulation\JEETACLossValid_e10_v23\refModel\e10_User_Rotor.dxf';
settingDXFTable.CurrentValue(contains(settingDXFTable.AutomationName,'FileName'))={testRotorDXFPath};
setMcadTableVariable(settingDXFTable,mcad)
mcad.GeometryExport()

%% WriteDXF

entitiesStatorStruct = readDXF(testStatorDXFPath)
entitiesStatorStruct = arrayfun(@(x) setfield(x, 'layer', 'stator'), entitiesStatorStruct);
% StatrDxf = filterEntitiesByAngle(entitiesStatorStruct, 45);
StatrDxf.entities=entitiesStatorStruct
StatrDxf.divisions=200
plotEntitiesStruct(StatrDxf)
NewtestStatorDXFPath=strsplit(testStatorDXFPath,'.')
NewtestStatorDXFPath=[NewtestStatorDXFPath{1},'Periodic','.dxf']
writeDXF(NewtestStatorDXFPath, StatrDxf)

%% RotorDXF
entitiesRotorStruct = readDXF(testRotorDXFPath);
entitiesRotorStruct = arrayfun(@(x) setfield(x, 'layer', 'rotor'), entitiesRotorStruct);
RotorDxf = filterEntitiesByAngle(entitiesRotorStruct, 45);
plotEntitiesStruct(RotorDxf)
NewtestRotorDXFPath=strsplit(testRotorDXFPath,'.')
NewtestRotorDXFPath=[NewtestRotorDXFPath{1},'Periodic','.dxf']

writeDXF(NewtestRotorDXFPath, RotorDxf)
%%
dxfList2Import(1).dxfPath=testStatorDXFPath
dxfList2Import(2).dxfPath=testRotorDXFPath

app=callJmag
app.Show
Model=app.GetCurrentModel
ItemList={'Stator','Rotor'};
dxfList2Import(1).sketchName=ItemList{1};
dxfList2Import(2).sketchName=ItemList{2};


geomApp=app.CreateGeometryEditor(0);
geomApp.Show
sketchs=ImportDXF2Geom(dxfList2Import,geomApp);

StatorGeomAssemTable    =getGeomSketchAssembleTable('Stator',geomApp);
RotorGeomAssembleTable  =getGeomSketchAssembleTable('Rotor',geomApp);

geomApp.Hide;
geomApp.Show
% Model.RestoreCadLink()

%% 정보 가져오기 -Arc/Line/Region별 정보가져오기 

[StatorAssemRegionTable,StatorGeomArcTable]=setGetGeomStatorNameNTable(StatorGeomAssemTable,geomApp);
%% Rotor Table
RotorGeomArcTable          =getArcDataTable(RotorGeomAssembleTable,geomApp);
RotorAssemRegionTable      =getRegionItemDataTable(RotorGeomAssembleTable,'Rotor',geomApp)
RotorAssemRegionTable=allocateSubSketchList2AssemRegionTable(RotorGeomAssembleTable,RotorAssemRegionTable,geomApp);
RotorRegionTablePerType = detRotorRegionTablePerType(RotorAssemRegionTable)
runnerType=checkInnerOuterMotor(StatorGeomArcTable,RotorGeomArcTable)

% RotorAssemRegionTable=setGetGeomRotorNameNTable(RotorGeomAssembleTable,geomApp)
%% 1.1 Define MachineData
MotorCADGeo=tempDefMCADMachineData4Scaling(mcad)
MachineData=MotorCADGeo
RotorOnePoleAngle=max(RotorGeomArcTable.EndVertexTabletheta);
% RotorOnePoleAngle=2*RotorOnePoleAngle
Poles       = 360/RotorOnePoleAngle;
PhaseNumber=3;
%% 1.1.1 Stator OneSlot Angle 알고리즘 고도화
StatorOneSlotAngle=findStatorOneSlotAngle(StatorGeomArcTable)
% NSPP
StatorOneSlotAngle=StatorOneSlotAngle
NSPP=RotorOnePoleAngle/StatorOneSlotAngle/PhaseNumber;
q=NSPP;
slots=NSPP*PhaseNumber*Poles;

%%[TF]
MachineData.Poles                 =Poles              ;   
MachineData.StatorOneSlotAngle    =StatorOneSlotAngle ;               
MachineData.PhaseNumber           =PhaseNumber        ;       
MachineData.NSPP                  =NSPP               ;   
MachineData.q                     =q                  ;
MachineData.slots                 =slots              ;   
MachineData.runnerType            =runnerType         ;
MachineData.StatorLength=MachineData.Stator_Lam_Lengthl

% SetGeomDesignTable
setGeomDesignTable('stack_length',MachineData.StatorLength,app);
setGeomDesignTable('SLOTS',slots,app);
setGeomDesignTable('POLES',Poles,app);
createCircPattern4StatorCore(MachineData,StatorAssemRegionTable,app)
createCircPattern4withInput(MachineData,StatorAssemRegionTable,'Area',app)
createCircPattern4withInput(MachineData,StatorAssemRegionTable,'Insulation',app)
createCircPattern4withInput(MachineData,StatorAssemRegionTable,'Conductor',app)
geomApp.Show


%% 2. Designer ImportGetPropertyTable

% Equation의 Ld,Lq값은 어떻게? 사전 해석?
app.SaveAs(jprojPath)
app.ImportDataFromGeometryEditor();
geomApp.SaveCurrent();
Model=app.GetCurrentModel

%% 2.1 [TC]Apply Template
%% [TM]
% app.ApplyAnalysisTemplate()
Model.DeleteStudy(InitialStudyName)
PWMStudyObj=Model.GetStudy('PWM');
clear Study
% Model.CreateStudy('Transient2D',StudyName)
%% 2.1.1 Study 설정 get & Set
% Study=Model.GetStudy(StudyName)
Study=PWMStudyObj;
propertiesTableWithValue=getJMagStudyProperties(Study)
Study.GetStudyProperties().SetValue('ModelThickness', MachineData.StatorLength)


%% 2.1.2 Circuit Magnet
magComponentList=duplicateACMagCircuitFromTemplate(PWMStudyObj,4);

%% 2.2 Designer Part Table
% isConductor=0  % conductor 임
% PartDataStruct=devDesignerPartDataTable(MachineData,app,isConductor);
PartStruct=getJMAGDesignerPartStruct(app);
%% 2.2.1 ConductorPartTable Sorting
ConductorPartTable=sortingConductorTableBySlot(PartStruct);
changeJMAGPartNameTable(ConductorPartTable,app);
 
%% 2.3 Make Set
SlotConductorSetName="SlotConductor";
Model.GetSetList().CreatePartSet("SlotConductor")
Model.GetSetList().GetSet("SlotConductor").SetUpdateByRelation(false)
Model.GetSetList().GetSet("SlotConductor").SetMatcherType("MatchNames")
Model.GetSetList().GetSet("SlotConductor").SetParameter("style", "prefix")
Model.GetSetList().GetSet("SlotConductor").SetParameter("text", "Stator/Slot")
Model.GetSetList().GetSet("SlotConductor").Rebuild()

RotorSetName="Rotor"
Model.GetSetList().CreatePartSet(RotorSetName)
Model.GetSetList().GetSet(RotorSetName).SetMatcherType("MatchNames")
Model.GetSetList().GetSet(RotorSetName).SetParameter("style", "prefix")
Model.GetSetList().GetSet(RotorSetName).SetParameter("text", "Rotor")
Model.GetSetList().GetSet(RotorSetName).Rebuild()


%% 2.5 Condition Seeting
%% 2.5.1 Rotationaly Periodic Boundary 

setRPBoundaryCondition(PWMStudyObj, StatorAssemRegionTable.distanceRFromCenter(1)/2);
%% 2.5.2 Motion 

RotConObj=PWMStudyObj.GetCondition('RotorMotion')
RotConObj.IsValid
RotConObj.AddSetFromModel('Rotor', 0)
%% 2.5.3 Conductor or Coil
% Template으로 변경 
PWMStudyObj.DeleteCondition("W1")
PWMStudyObj.DeleteCondition("V1")
PWMStudyObj.DeleteCondition("U1")
setJMAGFEMConductor(ConductorPartTable,PWMStudyObj)

%% 2.5.4Add FEM Conductor 4 Mag 
 setJMAGFEMConductor4Mag(PartStruct,magComponentList,StudyObj);

%% 3. Mesh Setting
% Element Size

% conductor 
MeshControlObj=PWMStudyObj.GetMeshControl()
%meshTotalPropertyTable
meshTotalPropertyTable=MeshControlObj.GetPropertyTable
meshTotalPropertyTable=char2CategoricalPropertiesTable(meshTotalPropertyTable)

% MeshControl Condition
NumConditions=MeshControlObj.NumConditions

MeshCondtionTable=table()
for MeshConditionIndex=1:NumConditions
    MeshCondtionObj=MeshControlObj.GetCondition(MeshConditionIndex-1);
    if MeshCondtionObj.IsValid
    MeshCondtionTable.MeshCondition(MeshConditionIndex)             =MeshCondtionObj;
    MeshCondtionTable.CondtionType{MeshConditionIndex}              ={MeshCondtionObj.GetType}
    MeshCondtionTable.Name{MeshConditionIndex}                      ={MeshCondtionObj.GetName}
    MeshCondtionTable.MeshCondtionPropertyTable(MeshConditionIndex) ={char2CategoricalPropertiesTable(MeshCondtionObj.GetPropertyTable)}
    MeshCondtionTable.Parts(MeshConditionIndex)                     ={MeshCondtionObj.GetParts};
    end
end

% Conductor
%% [ToManual]Error Due to Name
MeshCondtionTable.MeshCondition(contains([MeshCondtionTable{:,'Name'}{:}],'Conductor')').AddSetFromModel(SlotConductorSetName,0)
% core

% Magnet
subConObj=MeshCondtionTable.MeshCondition(MeshConditionIndex).Add
% Barrier?

% Skin Dpeth

% MeshCondtionTable.MeshCondition(contains([MeshCondtionTable{:,'CondtionType'}{:}],'SkinDepth')').AddSetFromModel(SlotConductorSetName,0)

%% 4. Material
%% 4.1 Load Material in matlab
%% 4.1.1 Syre Type
load('Z:\01_Codes_Projects\Torino_syRe\motorExamples\mot_01.mat');
BLKLABELS.materials=char(...
    mat.Stator.MatName,...
    mat.Rotor.MatName,...
    'N52M',...
    'Copper'...
    );  
% 'Magnet Operating Temperature
if any(unique(Magnetxy(:,9)) ~= 0)
PMTemp = mat.LayerMag.temp.temp(1,1);%20 C
end
stator_mat1 = BLKLABELS.materials(1,:);
stator_mat = strcat(stator_mat1,'Customized');
%'# New BH-curve data based on SyRe library
property = material_properties_iron(stator_mat1);
property.Type='Syre';
% Set Core Material
% syreMatProperties=fieldnames(property);
% save('syreMatProperties','syreMatProperties');
load('Z:\01_Codes_Projects\git_fork_emach\tools\material\syreMatProperties.mat')
%% 4.1.2 MCAD Type
CorefileName="Z:\01_Codes_Projects\git_fork_emach\tools\NO18_1160.mdb";
SteelName='NO18-1160'
mcad.ExportSolidMaterial(CorefileName,SteelName)
NO18_1160=readMCADMaterialDBFile(CorefileName);
TotalData_NO18_1160=converMCADCoreMagnetTable2CellFormat(NO18_1160,SteelName);
TotalData_NO18_1160.BHValueTable
TotalData_NO18_1160.MaxwellLossTable
% MCADMatProperties=NO18_1160.AutomationName
% save('MCADMatProperties','MCADMatProperties');

% mat =load('Z:\01_Codes_Projects\git_fork_emach\tools\NO18_1160.mat');


%% 4.2 Create Material in JMAG
JDesigner=app;
createCustomMaterialJMAG(app,TotalData_NO18_1160,SteelName)

%% Set Conductor Material
%% Set Material
ConductorPartCell={PartStruct(contains({PartStruct(:).Name}','Conductor')).Name};
for PartIndex=1:height(ConductorPartTable)
PWMStudyObj.SetMaterialByName(ConductorPartCell{PartIndex},"Copper")
PWMStudyObj.GetMaterial(ConductorPartCell{PartIndex}).SetValue("EddyCurrentCalculation", 1)
end
%% 'stator material
% stator_mat=BLKLABELS.materials(1,:);
% 'stator lanimation factor in %
stator_lamfactor=99.7;
% '#stator magnetic saturation factor in %
% stator_magSatfactor = 100;
% 'Electric conductivity of the stator
%Use Materials which contain Hysteresis Loops from stator: Yes(1) / No(0)
hysteresisloop_s=0; % 0= not use 
                    % 1=use
%Allow eddy current from stator : Yes(1) / No(0)
eddycurrent_s=0;    % 0= No eddy current 
                    % 1= Allow eddy current 
                    % 2= calculate distribution in steel plate 
stator_mat='NO18-1160';
setJMAGCoreMaterial(PWMStudyObj,'Stator/StatorCore',stator_mat,1,stator_lamfactor,hysteresisloop_s,eddycurrent_s)
%% 'Rotor Material
setJMAGCoreMaterial(PWMStudyObj,'Rotor/RotorCore',stator_mat,1,stator_lamfactor,hysteresisloop_s,eddycurrent_s)
%% 'MagNet Material
MagfileName="Z:\01_Codes_Projects\git_fork_emach\tools\N42EH.mdb";
% mcad.ExportSolidMaterial(MagfileName,'N42EH')
N42EH=readMCADMaterialDBFile(MagfileName);
% 
TotalDataN42EH=converMCADMagnetTable(N42EH);
TotalDataN42EH.MagnetTable


%% Equation
mcad=callMCAD
[~,Ld_mH]=mcad.GetVariable('InductanceLoad_D');
[~,Lq_mH]=mcad.GetVariable('InductanceLoad_Q');
Ld=mm2m(Ld_mH);
Lq=mm2m(Lq_mH);
Ld=num2str(Ld);
Lq=num2str(Lq);

[~,Psi]=mcad.GetVariable('FluxLinkageQAxisCurrent_D');
[~,PeakCurrent]=mcad.GetVariable('PeakCurrent');
[~,PhaseAdvance]=mcad.GetVariable('PhaseAdvance');
[Idpk,Iqpk]=pkbeta2dq(PeakCurrent,PhaseAdvance)


Psi=num2str(Psi);

mkDesignerEquation('Ld',Ld,PWMStudyObj);
mkDesignerEquation('Lq',Lq,PWMStudyObj);
mkDesignerEquation('Psi',Psi,PWMStudyObj);

%% Non Speed Control

NoSpeedStudy=app.GetModel("e10JFT047FeedbackControl_0").GetStudy("PWM_NospeedControl");
Idpk=num2str(Idpk);
Iqpk=num2str(Iqpk);
mkDesignerEquation('Idpk',Idpk,NoSpeedStudy);
mkDesignerEquation('Iqpk',Iqpk,NoSpeedStudy);


%% get PhiD, PhiQ, Ld, Lq
% Syre Format

dateString = '19-Nov-2023';

% 'InputFormat'을 사용하여 날짜 형식 지정
inputFormat = 'dd-MMM-yyyy';

% 'Locale'을 사용하여 로캘 지정 (예: 'en_US' 또는 'ko_KR')
locale = 'en_US';

% datetime 함수로 날짜 변환
dateValue = datetime(dateString, 'InputFormat', inputFormat, 'Locale', locale);

%% Result
% Simulation


%% MapTable - Field-Circuit
% Map Table is same MCADLabTable, Simulink Table


%% CLM
